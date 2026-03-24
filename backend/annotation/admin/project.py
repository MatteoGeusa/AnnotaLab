from django.contrib import admin
from django import forms
from unfold.admin import ModelAdmin, TabularInline
from django.utils.html import format_html, mark_safe
from django.urls import reverse, path
from django.utils.http import urlencode
from django.http import HttpResponse
from django.contrib import messages
import json
import re
from ..models import Project, Annotation, ProjectLogEntry
from ..services import parse_json_upload, process_uploaded_dataset
from ..mace_service import run_mace_for_project

class ProjectAdminForm(forms.ModelForm):
    """
    Custom form that adds non-model file inputs for uploading JSON configs.
    The uploaded file is parsed and stored directly into the JSONField on save.
    """
    upload_task_config = forms.FileField(
        required=False,
        label="Upload Task Config (JSON)",
        help_text="Upload a JSON file to overwrite the Task configuration (Labels, Questions)."
    )
    upload_gold_config = forms.FileField(
        required=False,
        label="Upload Gold Config (JSON)",
        help_text="Upload a JSON file to overwrite the Gold Units QC configuration."
    )
    upload_screening_config = forms.FileField(
        required=False,
        label="Upload Screening Config (JSON)",
        help_text="Upload a JSON file to configure the screening questionnaire (demographics, etc.)."
    )
    upload_codebook_content = forms.FileField(
        required=False,
        label="Upload Codebook (Markdown)",
        help_text="Upload a .md file to overwrite the theoretical/practical background."
    )
    upload_instructions_content = forms.FileField(
        required=False,
        label="Upload Instructions (Markdown)",
        help_text="Upload a .md file for task instructions shown before the practice task."
    )
    upload_practice_task_config = forms.FileField(
        required=False,
        label="Upload Practice Task (JSON)",
        help_text="Upload a JSON file with the practice task (text, gold_solution, hints)."
    )

    class Meta:
        model = Project
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get('is_active')
        documents_file = cleaned_data.get('documents_file')
        
        # We need to know if the project ALREADY has documents in the database
        has_existing_docs = False
        if self.instance.pk:
            has_existing_docs = self.instance.documents.filter(is_gold_unit=False).exists()

        # If the user tries to activate the project
        if is_active:
            # It's valid ONLY if:
            # 1. It already has documents in the DB
            # 2. OR it's being provided a new document file right now
            if not has_existing_docs and not documents_file:
                # We raise the error on the 'is_active' field
                self.add_error('is_active', "❌ Cannot Activate: No dataset found. Please upload a .jsonl file in 'Task Configuration' before setting the project to Active.")
        
        return cleaned_data

class ProjectLogInline(TabularInline):
    model = ProjectLogEntry
    extra = 0
    readonly_fields = ('timestamp', 'action', 'details')
    can_delete = False
    tab = True

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    # Columns visible in the project list view
    list_display = ('name', 'status_badge', 'documents_link', 'gold_units_link', 'enrollments_link', 'annotations_link', 'link_prolific','export_list_button')
    
    actions = ['run_mace_analysis']

    @admin.action(description="Run MACE Reliability Analysis on selected projects")
    def run_mace_analysis(self, request, queryset):
        for project in queryset:
            try:
                result = run_mace_for_project(project.id)
                if result.get("status") == "success":
                    self.message_user(request, f"{project.name}: {result['message']}", messages.SUCCESS)
                else:
                    self.message_user(request, f"{project.name}: {result.get('message', 'Error')}", messages.WARNING)
            except Exception as e:
                self.message_user(request, f"Error running MACE on {project.name}: {str(e)}", messages.ERROR)

    form = ProjectAdminForm
    readonly_fields = (
        'status_badge',
        'formatted_task_type_config', 
        'formatted_gold_config', 
        'formatted_screening_config',
        'formatted_codebook_content',
        'formatted_instructions_content',
        'formatted_practice_task_config',
    )
    
    tabs = [
        ("details", "Project Details"),
        ("training", "Training & Instructions"),
        ("config", "Task Configuration"),
        ("quality", "Quality & Gold"),
        ("launch", "Launch & Distribution"),
    ]

    inlines = [ProjectLogInline]

    
    fieldsets = (
        ("Project Details", {
            "fields": (("name", "slug"), "status", "is_active", "description", "informed_consent_config",),
            "classes": ("tab", "details"),
        }),

        ("Participant Training", {
            "classes": ("tab", "training"),
            "fields": (
                "enable_screening",
                "formatted_screening_config",
                "upload_screening_config",
                "enable_codebook",
                "formatted_codebook_content",
                "upload_codebook_content",
            ),
            "description": """
                <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #10B981; color: #ddd;">
                        <b>📋 Screening:</b><br>Initial questionnaire for demographics and metadata.
                    </div>
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #A78BFA; color: #ddd;">
                        <b>📖 Codebook:</b><br>Theoretical/practical background instructions (Markdown).
                    </div>
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #F59E0B; color: #ddd;">
                        <b>📝 Instructions:</b><br>Task instructions + optional guided practice task.
                    </div>
                </div>
            """
        }),

        ("Instructions & Practice", {
            "classes": ("tab", "training"),
            "fields": (
                "enable_instructions",
                "formatted_instructions_content",
                "upload_instructions_content",
                "formatted_practice_task_config",
                "upload_practice_task_config",
                "practice_task_required",
            ),
            "description": """
                <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #F59E0B; color: #ddd;">
                        <b>📝 Instructions:</b><br>Markdown content shown to annotators before the task.
                    </div>
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #EC4899; color: #ddd;">
                        <b>🎯 Practice Task:</b><br>Optional guided practice with correct solution and hints.
                    </div>
                </div>
            """
        }),

        ("Task Configuration", {
            "classes": ("tab", "config"),
            "fields": (
                "formatted_task_type_config",
                "upload_task_config",
                "documents_file",
                ("dataset_text_key", "dataset_id_key"),
            ),
            "description": """
                <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                    <div style="flex: 1; background: #2a2a2a; padding: 15px; border-left: 4px solid #3B82F6; color: #ddd; border-radius: 4px;">
                        <b style="color: #60a5fa; font-size: 1.1em;">⚙️ Task Design</b><br>
                        Configure the labeling interface (labels, questions, layout).
                    </div>
                    <div style="flex: 1; background: #2a2a2a; padding: 15px; border-left: 4px solid #10B981; color: #ddd; border-radius: 4px;">
                        <b style="color: #34d399; font-size: 1.1em;">📊 Data Import</b><br>
                        Upload your <b>.jsonl</b> dataset. Each line must be a JSON object with at least a text field.
                    </div>
                </div>
            """
        }),

        ("Quality / Monitoring", {
            "classes": ("tab", "quality"),
            "fields": (
                "enable_gold_units",
                "formatted_gold_config",
                "upload_gold_config",
                "gold_units_file",
            ),
            "description": """
                <div style="display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px;">
                    <div style="background: #1e293b; padding: 15px; border-left: 4px solid #8b5cf6; color: #e2e8f0; border-radius: 4px;">
                        <b style="color: #a78bfa; font-size: 1.1em;">🤖 MACE (Multi-Annotator Competence Estimation)</b><br>
                        Use MACE to estimate annotator reliability and infer the most likely "true" labels even without gold units. 
                        <i>Run this analysis from the project list 'Actions' menu once you have gathered annotations.</i>
                    </div>

                    <div style="background: #1e293b; padding: 15px; border-left: 4px solid #f59e0b; color: #e2e8f0; border-radius: 4px;">
                        <b style="color: #fbbf24; font-size: 1.1em;">🛡️ Gold Units (Ground Truth)</b><br>
                        Manually verified units used to "test" annotators in real-time. 
                        Configure the strategy above and upload the Gold dataset below.
                    </div>
                </div>
            """
        }),

        ("Distribution & Launch", {
            "classes": ("tab", "launch"),
            "fields": (
                "distribution_strategy",
                ("min_annotations_per_doc", "max_annotations_per_doc"),
                ("block_size", "annotators_per_block"),
                "prioritize_unannotated"
            ),
            "description": "Configure how documents are served to workers."
        }),
    )

    class Media:
        css = {
            'all': ('css/admin_project.css',)
        }
        js = ('js/admin_project.js',)

    def _colorize_json(self, json_str):
        """Apply simple syntax highlighting to a JSON string for HTML display."""
        # Escape HTML first
        from django.utils.html import escape
        escaped = escape(json_str)
        # Highlight keys ("key":)
        escaped = re.sub(
            r'&quot;([^&]+?)&quot;(?=\s*:)',
            r'<span class="json-key">&quot;\1&quot;</span>',
            escaped
        )
        # Highlight string values (: "value")
        escaped = re.sub(
            r':\s*&quot;([^&]*?)&quot;',
            r': <span class="json-string">&quot;\1&quot;</span>',
            escaped
        )
        # Highlight numbers
        escaped = re.sub(
            r':\s*(\d+\.?\d*)',
            r': <span class="json-number">\1</span>',
            escaped
        )
        # Highlight booleans
        escaped = re.sub(
            r'\b(true|false|null)\b',
            r'<span class="json-bool">\1</span>',
            escaped
        )
        return escaped

    def _render_config_block(self, config_data, title, icon):
        """Render a JSON config as a styled HTML block."""
        if not config_data:
            return format_html(
                '<div class="config-empty">'
                '<span class="empty-icon">{}</span>'
                '<span>No {} configured yet. Upload a JSON file above.</span>'
                '</div>',
                icon, title.lower()
            )

        # Ensure important keys are on top if it's a dictionary
        if isinstance(config_data, dict):
            priority_keys = ["task_type", "min_accuracy_required", "gold_injection_frequency", "continuous_exclusion"]
            ordered_data = {k: config_data[k] for k in priority_keys if k in config_data}
            for k, v in config_data.items():
                if k not in ordered_data:
                    ordered_data[k] = v
            config_data = ordered_data

        json_str = json.dumps(config_data, indent=4)
        colorized = self._colorize_json(json_str)

        return format_html(
            '<div class="json-config-display break-words max-w-none py-3 text-sm bg-base-50 border border-base-200 font-medium px-4 rounded-default shadow-xs dark:border-base-700 dark:bg-base-800">'
            '  <div class="config-header" style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(0,0,0,0.05); color: #64748b;">'
            '    <span class="config-icon">{icon}</span> <strong>{title}</strong>'
            '  </div>'
            '  <pre style="margin: 0; background: transparent; border: none; padding: 0; font-family: \'JetBrains Mono\', monospace; font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; color: inherit;">{code}</pre>'
            '</div>',
            icon=icon,
            title=title,
            code=mark_safe(colorized)
        )

    @admin.display(description="Task Config")
    def formatted_task_type_config(self, obj):
        return self._render_config_block(obj.task_type_config, 'Task Configuration', '⚙️')

    @admin.display(description="Gold Config")
    def formatted_gold_config(self, obj):
        return self._render_config_block(obj.gold_config, 'Gold Units Configuration', '🛡️')

    @admin.display(description="Screening Config")
    def formatted_screening_config(self, obj):
        return self._render_config_block(obj.screening_config, 'Screening Configuration', '📋')

    def _render_markdown_block(self, md_text, title, icon):
        """Convert Markdown text to styled HTML for admin display."""
        from django.utils.html import escape
        
        if not md_text or not md_text.strip():
            return format_html(
                '<div class="config-empty">'
                '<span class="empty-icon">{}</span>'
                '<span>No {} configured yet. Upload a Markdown file above.</span>'
                '</div>',
                icon, title.lower()
            )

        text = escape(md_text)

        # Headers
        text = re.sub(r'^### (.+)$', r'<h4 style="font-size:14px;font-weight:600;color:#64748b;margin:16px 0 6px;">\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h3 style="font-size:16px;font-weight:600;color:#306ee8;margin:20px 0 8px;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h2 style="font-size:18px;font-weight:700;color:inherit;margin:24px 0 10px;padding-bottom:6px;border-bottom:1px solid rgba(128,128,128,0.2);">\1</h2>', text, flags=re.MULTILINE)

        # Bold + italic
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic with underscores (_text_) and asterisks (*text*)
        text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', text)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

        # Inline code
        text = re.sub(r'`(.+?)`', r'<code style="background:rgba(128,128,128,0.15);padding:1px 5px;border-radius:3px;font-size:0.9em;">\1</code>', text)

        # Blockquotes
        text = re.sub(
            r'^&gt; (.+)$',
            r'<div style="border-left:3px solid #306ee8;padding:6px 12px;margin:8px 0;background:rgba(48,110,232,0.06);border-radius:0 6px 6px 0;font-size:0.92em;">\1</div>',
            text, flags=re.MULTILINE
        )

        # Horizontal rules
        text = re.sub(r'^---$', r'<hr style="border:none;border-top:1px solid rgba(128,128,128,0.2);margin:20px 0;">', text, flags=re.MULTILINE)

        # Unordered list items (handle nested with 2+ spaces)
        text = re.sub(
            r'^  - (.+)$',
            r'<div style="padding-left:28px;margin:3px 0;"><span style="color:#306ee8;margin-right:6px;">◦</span>\1</div>',
            text, flags=re.MULTILINE
        )
        text = re.sub(
            r'^- (.+)$',
            r'<div style="padding-left:8px;margin:4px 0;"><span style="color:#306ee8;margin-right:6px;">•</span>\1</div>',
            text, flags=re.MULTILINE
        )

        # Paragraphs — wrap remaining non-tag lines
        lines = text.split('\n')
        processed = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('<'):
                processed.append(f'<p style="margin:6px 0;line-height:1.7;">{stripped}</p>')
            else:
                processed.append(line)
        text = '\n'.join(processed)

        # Remove empty paragraphs
        text = re.sub(r'<p[^>]*>\s*</p>', '', text)

        return format_html(
            '<div class="json-config-display break-words max-w-none py-3 text-sm bg-base-50 border border-base-200 font-medium px-4 rounded-default shadow-xs dark:border-base-700 dark:bg-base-800">'
            '  <div class="config-header" style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(0,0,0,0.05); color: #64748b;">'
            '    <span class="config-icon">{icon}</span> <strong>{title}</strong>'
            '  </div>'
            '  <div style="font-family: \'Outfit\', \'Inter\', sans-serif; font-size: 13px; line-height: 1.7; color: inherit;">{content}</div>'
            '</div>',
            icon=icon,
            title=title,
            content=mark_safe(text)
        )

    @admin.display(description="Codebook Content")
    def formatted_codebook_content(self, obj):
        return self._render_markdown_block(obj.codebook_content, 'Codebook Materials', '📖')

    @admin.display(description="Instructions Content")
    def formatted_instructions_content(self, obj):
        return self._render_markdown_block(obj.instructions_content, 'Task Instructions', '📝')

    @admin.display(description="Practice Task Config")
    def formatted_practice_task_config(self, obj):
        return self._render_config_block(obj.practice_task_config, 'Practice Task', '🎯')

    def get_urls(self):
        urls = super(ProjectAdmin, self).get_urls()
        my_urls = [
            path(
                '<path:object_id>/export/', 
                self.admin_site.admin_view(self.download_export_view), 
                name='project_export_jsonl'
            ),
        ]
        return my_urls + urls

    def download_export_view(self, request, object_id):
        project = self.get_object(request, object_id)
        
        response = HttpResponse(content_type='application/x-jsonlines')
        filename = f"{project.name.replace(' ', '_').lower()}_annotations.jsonl"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        annotations = Annotation.objects.filter(
            document__project=project,
            document__is_gold_unit=False  # Exclude gold units
        ).select_related('document', 'annotator')

        for ann in annotations:
            raw_result = ann.result
            formatted_markers = []
            raw_spans = raw_result.get('spans', [])
            
            if isinstance(raw_spans, list):
                for span in raw_spans:
                    formatted_markers.append({
                        "startIndex": span.get('start'),
                        "endIndex": span.get('end'),
                        "type": span.get('label'),
                        "text": span.get('text')
                    })

            output_obj = {
                "_id": ann.document.external_id,
                "conspiracy": raw_result.get('classification'),
                "markers": formatted_markers,
                "subreddit": ann.document.metadata.get('subreddit', 'unknown'),
                "annotator": ann.annotator.prolific_pid
            }
            response.write(json.dumps(output_obj) + '\n')

        return response


    @admin.display(description="Export")
    def export_list_button(self, obj):
        url = reverse('admin:project_export_jsonl', args=[obj.pk])
        return format_html(
            '''
            <a href="{}" 
               class="bg-primary-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-primary-700 transition inline-block whitespace-nowrap text-center"
               title="Download .jsonl">
               ⬇ JSONL
            </a>
            ''',
            url
        )


    @admin.display(description="Status", ordering='status')
    def status_badge(self, obj):
        colors = {
            'DRAFT': ('#4b5563', '#f3f4f6'), # Gray
            'LIVE': ('#065f46', '#6ee7b7'),  # Green
            'PAUSED': ('#92400e', '#fde68a'), # Amber/Yellow
            'COMPLETED': ('#1e40af', '#bfdbfe'), # Blue
        }
        bg, fg = colors.get(obj.status, ('#7f1d1d', '#fca5a5'))
        
        return mark_safe(
            f'<span style="display:inline-block;padding:4px 12px;border-radius:20px;'
            f'font-size:11px;font-weight:700;letter-spacing:0.5px;white-space:nowrap;'
            f'background:{bg};color:{fg};">● {obj.status}</span>'
        )

    @admin.display(description="Documents")
    def documents_link(self, obj):
        count = obj.documents.filter(is_gold_unit=False).count()
        url = (
            reverse("admin:annotation_documentproxy_changelist")
            + "?"
            + urlencode({"project__id": f"{obj.id}", "o": "1"})
        )
        return format_html(
            '''
            <a href="{}" 
               class="bg-blue-600 text-white px-3 py-1 rounded text-xs font-bold hover:bg-blue-700 transition inline-block text-center min-w-[120px] whitespace-nowrap"
               title="Manage Real Documents">
               -> ({}) Manage Docs
            </a>
            ''',
            url, count
        )

    @admin.display(description="Gold Units")
    def gold_units_link(self, obj):
        count = obj.documents.filter(is_gold_unit=True).count()
        url = (
            reverse("admin:annotation_goldunitproxy_changelist")
            + "?"
            + urlencode({"project__id": f"{obj.id}", "o": "1"})
        )
        return format_html(
            '''
            <a href="{}" 
               class="bg-amber-500 text-white px-3 py-1 rounded text-xs font-bold hover:bg-amber-600 transition inline-block text-center min-w-[120px] whitespace-nowrap"
               title="Manage Gold Units">
               -> ({}) Manage Gold
            </a>
            ''',
            url, count
        )

    @admin.display(description="Annotations", ordering='-created_at')
    def annotations_link(self, obj):
        count = Annotation.objects.filter(document__project=obj).count()
        url = (
            reverse("admin:annotation_annotation_changelist")
            + "?"
            + urlencode({
                "document__project__id": f"{obj.id}", 
                "o": "1",
                "category": "regular"
            })
        )
        
        bg_class = "bg-green-600 hover:bg-green-700" if count > 0 else "bg-gray-400 hover:bg-gray-500"
        
        return format_html(
            '''
            <a href="{}" 
               class="{} text-white px-3 py-1 rounded text-xs font-bold transition inline-block text-center min-w-[120px] whitespace-nowrap"
               title="Manage Annotations">
               -> ({}) Manage Annotations
            </a>
            ''',
            url, bg_class, count
        )

    @admin.display(description="Workers")
    def enrollments_link(self, obj):
        count = obj.enrollments.count()
        url = (
            reverse("admin:annotation_projectenrollment_changelist")
            + "?"
            + urlencode({"project__id": f"{obj.id}"})
        )
        return format_html(
            '''
            <a href="{}" 
               style="background: #fbbf24; color: #1f2937;"
               class="px-3 py-1 rounded text-xs font-bold transition inline-block text-center min-w-[120px] whitespace-nowrap"
               title="Manage Workers">
               -> ({}) Manage Workers
            </a>
            ''',
            url, count
        )
    
    @admin.display(description="Link (Prolific)")
    def link_prolific(self, obj):
        # Format: http://localhost:5173/nome-studio?PROLIFIC_PID=
        display_url = f"http://localhost:5173/{obj.slug}?PROLIFIC_PID="
        test_url = f"http://localhost:5173/{obj.slug}?PROLIFIC_PID=TEST_USER_001"
        return format_html(
            '''
            <div style="display:flex; align-items:center; gap:8px; min-width:250px;">
                <code style="
                    background:#1e1e1e; color:#60a5fa;
                    padding:4px 8px; border-radius:4px;
                    font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
                    border:1px solid #333; flex:1;
                ">{}</code>
                <a href="{}" target="_blank"
                   style="flex-shrink:0; background:#2563eb; color:white; padding:3px 8px;
                          border-radius:4px; font-size:11px; text-decoration:none; font-weight:bold;"
                   title="Open with TEST_USER_001">
                   ↗ Test
                </a>
            </div>
            ''',
            display_url,
            test_url,
        )


    def save_model(self, request, obj, form, change):
        is_new = not obj.pk
        old_status = None
        if not is_new:
            old_status = Project.objects.get(pk=obj.pk).status

        super(ProjectAdmin, self).save_model(request, obj, form, change)

        # --- Logging ---
        if is_new:
            ProjectLogEntry.objects.create(
                project=obj,
                action="Project Created",
                details=f"Project '{obj.name}' initialized as Draft."
            )
        elif old_status != obj.status:
            ProjectLogEntry.objects.create(
                project=obj,
                action="Status Changed",
                details=f"Project changed from {old_status} to {obj.status}."
            )

        # --- Process uploaded Task Config JSON ---
        task_config_file = form.cleaned_data.get('upload_task_config')
        if task_config_file:
            try:
                obj.task_type_config = parse_json_upload(task_config_file)
                obj.save(update_fields=['task_type_config'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Config Updated",
                    details="Task Configuration (labels/questions) uploaded via JSON file."
                )
                messages.success(request, "Task Configuration updated from JSON file!")
            except Exception as e:
                messages.error(request, f"Task Config Error: {str(e)}")

        # --- Process uploaded Gold Config JSON ---
        gold_config_file = form.cleaned_data.get('upload_gold_config')
        if gold_config_file:
            try:
                obj.gold_config = parse_json_upload(gold_config_file)
                obj.save(update_fields=['gold_config'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Gold Config Updated",
                    details="Gold Units quality control strategy updated via JSON file."
                )
                messages.success(request, "Gold Units Configuration updated from JSON file!")
            except Exception as e:
                messages.error(request, f"Gold Config Error: {str(e)}")

        # --- Process uploaded Screening Config JSON ---
        screening_config_file = form.cleaned_data.get('upload_screening_config')
        if screening_config_file:
            try:
                parsed = parse_json_upload(screening_config_file)
                if not isinstance(parsed, list):
                    raise ValueError("Screening config must be a JSON array of questions.")
                obj.screening_config = parsed
                obj.save(update_fields=['screening_config'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Screening Updated",
                    details=f"Screening questionnaire updated ({len(parsed)} questions)."
                )
                messages.success(request, f"Screening Configuration updated! {len(parsed)} question(s) loaded.")
            except Exception as e:
                messages.error(request, f"Screening Config Error: {str(e)}")

        # --- Process uploaded Codebook Markdown ---
        codebook_file = form.cleaned_data.get('upload_codebook_content')
        if codebook_file:
            try:
                content = codebook_file.read().decode('utf-8')
                obj.codebook_content = content
                obj.save(update_fields=['codebook_content'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Codebook Updated",
                    details="Theoretical background (Codebook) updated via Markdown file."
                )
                messages.success(request, "Codebook content updated from file!")
            except Exception as e:
                messages.error(request, f"Codebook Upload Error: {str(e)}")

        # --- Process uploaded Instructions Markdown ---
        instructions_file = form.cleaned_data.get('upload_instructions_content')
        if instructions_file:
            try:
                content = instructions_file.read().decode('utf-8')
                obj.instructions_content = content
                obj.save(update_fields=['instructions_content'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Instructions Updated",
                    details="Task instructions updated via Markdown file."
                )
                messages.success(request, "Instructions content updated from file!")
            except Exception as e:
                messages.error(request, f"Instructions Upload Error: {str(e)}")

        # --- Process uploaded Practice Task JSON ---
        practice_file = form.cleaned_data.get('upload_practice_task_config')
        if practice_file:
            try:
                obj.practice_task_config = parse_json_upload(practice_file)
                obj.save(update_fields=['practice_task_config'])
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Practice Task Updated",
                    details="Guided practice task configuration updated via JSON file."
                )
                messages.success(request, "Practice Task configuration updated from JSON file!")
            except Exception as e:
                messages.error(request, f"Practice Task Config Error: {str(e)}")

        # --- Process Documents File ---
        if 'documents_file' in form.changed_data and obj.documents_file:
            try:
                count, import_warnings = process_uploaded_dataset(obj, obj.documents_file)
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Dataset Imported",
                    details=f"Successfully imported {count} regular documents."
                )
                messages.success(request, f"Regular documents import successful! Created {count} documents.")
                for warn in import_warnings:
                    messages.warning(request, f"⚠️ {warn}")
            except Exception as e:
                messages.error(request, f"Documents import error: {str(e)}")

        # --- Process Gold Units File ---
        if 'gold_units_file' in form.changed_data and obj.gold_units_file:
            try:
                count, import_warnings = process_uploaded_dataset(obj, obj.gold_units_file)
                ProjectLogEntry.objects.create(
                    project=obj,
                    action="Gold Units Imported",
                    details=f"Successfully imported {count} gold units."
                )
                messages.success(request, f"Gold units import successful! Created {count} units.")
                for warn in import_warnings:
                    messages.warning(request, f"⚠️ {warn}")
            except Exception as e:
                messages.error(request, f"Gold units import error: {str(e)}")