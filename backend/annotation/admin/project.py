from django.contrib import admin
from django import forms
from unfold.admin import ModelAdmin
from django.utils.html import format_html, mark_safe
from django.urls import reverse, path
from django.utils.http import urlencode
from django.http import HttpResponse
from django.contrib import messages
import json
import re
from ..models import Project, Annotation
from ..services import parse_json_upload, process_uploaded_dataset


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
                # We raise the error on the 'is_active' field so it shows up in Step 4
                self.add_error('is_active', "❌ Cannot Activate: No dataset found. Please upload a .jsonl file in 'Step 3' before setting the project to Active.")
        
        return cleaned_data

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    # Columns visible in the project list view
    list_display = ('name', 'documents_link', 'gold_units_link', 'enrollments_link', 'annotations_link', 'link_prolific','export_list_button')
    
    form = ProjectAdminForm
    readonly_fields = (
        'formatted_task_type_config', 
        'formatted_gold_config', 
        'formatted_screening_config',
        'formatted_codebook_content',
    )
    
    fieldsets = (
        ("Project Details", {
            "fields": (("name", "slug"), "description", "informed_consent_config",),
            "classes": ("tab",),
        }),

        ("Step 1: Participant Training", {
            "classes": ("tab",),
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
                </div>
            """
        }),

        ("Step 2: Task Design", {
            "classes": ("tab",),
            "fields": (
                "formatted_task_type_config",
                "upload_task_config",
                "enable_gold_units",
                "formatted_gold_config",
                "upload_gold_config",
            ),
            "description": """
                <div style="display: flex; gap: 10px;">
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #3B82F6; color: #ddd;">
                        <b>⚙️ Task:</b><br>The actual labeling configuration (labels, questions).
                    </div>
                    <div style="flex: 1; background: #2a2a2a; padding: 10px; border-left: 4px solid #FFB700; color: #ddd;">
                        <b>🛡️ Gold Units:</b><br>Quality control strategy and injection frequency.
                    </div>
                </div>
            """
        }),

        ("Step 3: Data Import", {
            "classes": ("tab",),
            "fields": (
                ("dataset_text_key", "dataset_id_key"),
                ("documents_file","gold_units_file")
            ),
            "description": """
                Upload <b>.jsonl</b> files where each line is a JSON object.<br><br>
                <b>Supported Fields:</b>
                <ul style="margin-left: 20px; list-style-type: disc; margin-bottom: 10px;">
                    <li><b>Text</b>: Key corresponding to 'Dataset text key' (default: <code>text</code>).</li>
                    <li><b>ID</b>: Key corresponding to 'Dataset id key' (default: <code>_id</code>).</li>
                    <li><b>gold_solution</b> (json): [Required for Gold Units] The correct solution for quality control.</li>
                    <li><b>metadata</b> (json): Optional metadata context.</li>
                </ul>
                <div style="background: #2a2a2a; padding: 10px; border-left: 4px solid #FFB700; color: #ddd;">
                    <b>💡 Documents vs Gold Units:</b><br>
                    - <b>Documents File</b>: Upload real data to be annotated.<br>
                    - <b>Gold Units File</b>: Upload quality control units with solutions.
                </div>
            """
        }),

        ("Step 4: Distribution & Launch", {
            "classes": ("tab",),
            "fields": (
                "is_active",
                "distribution_strategy",
                "target_tasks_per_annotator",
                ("min_annotations_per_doc", "max_annotations_per_doc"),
                "prioritize_unannotated"
            )
        })
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

    @admin.display(description="Codebook Content")
    def formatted_codebook_content(self, obj):
        # Even though it's markdown, we render it in the same code-style block
        return self._render_config_block(obj.codebook_content, 'Codebook Materials', '📖')

    def get_urls(self):
        urls = super().get_urls()
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
               class="bg-primary-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-primary-700 transition"
               title="Download .jsonl">
               ⬇ JSONL
            </a>
            ''',
            url
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
               class="bg-blue-600 text-white px-3 py-1 rounded text-xs font-bold hover:bg-blue-700 transition inline-block text-center min-w-[120px]"
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
               class="bg-amber-500 text-white px-3 py-1 rounded text-xs font-bold hover:bg-amber-600 transition inline-block text-center min-w-[120px]"
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
               class="{} text-white px-3 py-1 rounded text-xs font-bold transition inline-block text-center min-w-[120px]"
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
               class="px-3 py-1 rounded text-xs font-bold transition inline-block text-center min-w-[120px]"
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
            <div style="display:flex; align-items:center; gap:8px; min-width:350px;">
                <code style="
                    background:#1e1e1e; color:#60a5fa;
                    padding:4px 8px; border-radius:4px;
                    font-size:12px; word-break:break-all;
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
        super().save_model(request, obj, form, change)

        # --- Process uploaded Task Config JSON ---
        task_config_file = form.cleaned_data.get('upload_task_config')
        if task_config_file:
            try:
                obj.task_type_config = parse_json_upload(task_config_file)
                obj.save(update_fields=['task_type_config'])
                messages.success(request, "Task Configuration updated from JSON file!")
            except Exception as e:
                messages.error(request, f"Task Config Error: {str(e)}")

        # --- Process uploaded Gold Config JSON ---
        gold_config_file = form.cleaned_data.get('upload_gold_config')
        if gold_config_file:
            try:
                obj.gold_config = parse_json_upload(gold_config_file)
                obj.save(update_fields=['gold_config'])
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
                messages.success(request, f"Screening Configuration updated! {len(parsed)} question(s) loaded.")
            except Exception as e:
                messages.error(request, f"Screening Config Error: {str(e)}")

        # --- Process uploaded Codebook Markdown ---
        codebook_file = form.cleaned_data.get('upload_codebook_content')
        if codebook_file:
            try:
                # Read as text
                content = codebook_file.read().decode('utf-8')
                obj.codebook_content = content
                obj.save(update_fields=['codebook_content'])
                messages.success(request, "Codebook content updated from file!")
            except Exception as e:
                messages.error(request, f"Codebook Upload Error: {str(e)}")

        # --- Process Documents File ---
        if 'documents_file' in form.changed_data and obj.documents_file:
            try:
                count, import_warnings = process_uploaded_dataset(obj, obj.documents_file)
                messages.success(request, f"Regular documents import successful! Created {count} documents.")
                for warn in import_warnings:
                    messages.warning(request, f"⚠️ {warn}")
            except Exception as e:
                messages.error(request, f"Documents import error: {str(e)}")

        # --- Process Gold Units File ---
        if 'gold_units_file' in form.changed_data and obj.gold_units_file:
            try:
                count, import_warnings = process_uploaded_dataset(obj, obj.gold_units_file)
                messages.success(request, f"Gold units import successful! Created {count} units.")
                for warn in import_warnings:
                    messages.warning(request, f"⚠️ {warn}")
            except Exception as e:
                messages.error(request, f"Gold units import error: {str(e)}")
