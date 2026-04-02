from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin, TabularInline
from django.utils.html import format_html, mark_safe
from django.urls import reverse, path
from django.utils.http import urlencode
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
import json
import re
from ..models import Project, Annotation, ProjectLogEntry
from ..services import parse_json_upload, process_uploaded_dataset, ProjectService
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
        documents_file = cleaned_data.get('documents_file')
        status = cleaned_data.get('status')
        
        # If the user tries to set the project to LIVE
        if status == 'LIVE':
            # Check if there are already documents in the DB
            has_existing_docs = self.instance.documents.filter(is_gold_unit=False).exists() if self.instance.pk else False
            
            # We allow going LIVE ONLY if:
            # 1. We already have documents in DB
            # 2. OR we are uploading a NEW file right now (which will be processed in save_model)
            if not has_existing_docs and not documents_file:
                error_msg = "Cannot Set to LIVE: No dataset found. Please upload a .jsonl file in 'Task Configuration' before setting the project status to Live."
                self.add_error('status', error_msg)
        
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
    list_display = ('project_name_link', 'status_badge', 'documents_link', 'gold_units_link', 'enrollments_link', 'annotations_link', 'link_prolific', 'export_list_button')
    
    @admin.display(description="Project Name", ordering='name')
    def project_name_link(self, obj):
        url = reverse('admin:annotation_project_change', args=[obj.pk])
        if obj.is_published:
            return format_html(
                '<a href="{}" style="font-weight:700; color:#3b82f6; text-decoration:none;" title="View read-only configuration">{} 🔒</a>',
                url, obj.name
            )
        return format_html('<a href="{}" style="font-weight:700; text-decoration:none; color:inherit;">{}</a>', url, obj.name)

    actions = []
    form = ProjectAdminForm
    readonly_fields = (
        'status_notice',
        'status_badge',
        'formatted_task_type_config', 
        'formatted_screening_config',
        'formatted_codebook_content',
        'formatted_instructions_content',
        'formatted_practice_task_config',
    )
    
    tabs = [
        ("details", "Project Details"),
        ("config", "Task Configuration"),
        ("training", "Training & Instructions"),
        ("quality", "Quality / Monitoring"),
        ("distribution", "Distribution & Launch"),
        ("log", "Activity Log"),
    ]

    inlines = [ProjectLogInline]

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and (obj.is_published or obj.status == 'LIVE'):
            locked = ['name', 'slug', 'description', 'informed_consent_config', 'dataset_text_key', 'dataset_id_key', 'enable_screening', 'enable_codebook', 'enable_instructions', 'enable_practice_task', 'practice_task_required', 'enable_gold_units', 'gold_injection_frequency', 'min_accuracy_required', 'min_gold_before_eval', 'distribution_strategy', 'min_annotations_per_doc', 'max_annotations_per_doc', 'block_size', 'annotators_per_block', 'prioritize_unannotated', 'documents_file', 'gold_units_file', 'prolific_completion_code']
            for f in locked:
                if f not in readonly: readonly.append(f)
        return readonly

    def get_fieldsets(self, request, obj=None):
        """Dynamically inject status notice into all tab descriptions."""
        notice_html = ""
        if obj:
            if obj.is_published:
                clone_url = reverse('admin:project_quick_clone', args=[obj.pk])
                notice_html = format_html(
                    '''
                    <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 16px; border-radius: 4px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px;">
                        <div style="line-height: 1.5;">
                            <b style="color: #f59e0b; font-size: 1.1em;">🔒 Progetto Ufficiale & Bloccato</b><br>
                            <span style="color: #94a3b8;">La configurazione è sigillata per integrità dati. Per modifiche strutturali, clona il progetto.</span>
                        </div>
                        <button type="button" onclick="quickCloneProject(this, '{}', '{}', true)" style="background: #f59e0b; color: white; padding: 8px 16px; border-radius: 6px; font-weight: 800; border:none; cursor:pointer; font-size: 12px;">📋 CLONA PROGETTO</button>
                    </div>
                    ''',
                    clone_url, obj.name
                )
            elif obj.status == 'LIVE':
                draft_url = reverse('admin:project_set_status', args=[obj.pk])
                notice_html = format_html(
                    '''
                    <div style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px;">
                        <div style="line-height: 1.5;">
                            <b style="color: #60a5fa; font-size: 1.1em;">▶️ Playground Attivo (LIVE)</b><br>
                            <span style="color: #94a3b8;">Il progetto è in sola lettura durante i test. Torna in Draft per sbloccare i campi.</span>
                        </div>
                        <button type="button" onclick="quickUpdateStatus(this, '{}', 'DRAFT', 'Draft')" style="background: #3b82f6; color: white; padding: 8px 16px; border-radius: 6px; font-weight: 800; border:none; cursor:pointer; font-size: 12px;">📁 TORNA IN DRAFT</button>
                    </div>
                    ''',
                    draft_url
                )

        # Standard fieldsets but with notice_html prepended to descriptions
        return (
            ("Project Details", {
                "fields": (("name", "slug"), "description", "informed_consent_config",),
                "classes": ("tab", "details"),
                "description": notice_html
            }),
            ("Task Configuration", {
                "classes": ("tab", "config"),
                "fields": (
                    "formatted_task_type_config",
                    "upload_task_config",
                    "documents_file",
                    ("dataset_text_key", "dataset_id_key"),
                ),
                "description": mark_safe(f"{notice_html}<div style='display:flex; gap:10px; margin-top:20px;'>\
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #3B82F6; color:#ddd; border-radius:4px;'>\
                        <b style='color:#60a5fa; font-size:1.1em;'>⚙️ Task Design</b><br>Labels, Questions, Layout.\
                    </div>\
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #10B981; color:#ddd; border-radius:4px;'>\
                        <b style='color:#34d399; font-size:1.1em;'>📊 Data Import</b><br>Upload .jsonl dataset.\
                    </div>\
                </div>")
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
                "description": mark_safe(f"{notice_html}<div style='display:flex; gap:10px; margin-top:10px;'>\
                    <div style='flex:1; background:#2a2a2a; padding:10px; border-left:4px solid #10B981; color:#ddd;'><b>📋 Screening</b></div>\
                    <div style='flex:1; background:#2a2a2a; padding:10px; border-left:4px solid #A78BFA; color:#ddd;'><b>📖 Codebook</b></div>\
                </div>")
            }),
            ("Instructions & Practice", {
                "classes": ("tab", "training"),
                "fields": (
                    "enable_instructions",
                    "formatted_instructions_content",
                    "upload_instructions_content",
                    "enable_practice_task",
                    "formatted_practice_task_config",
                    "upload_practice_task_config",
                    "practice_task_required",
                ),
                "description": mark_safe(f"{notice_html}<div style='display:flex; gap:10px; margin-top:10px;'>\
                    <div style='flex:1; background:#2a2a2a; padding:10px; border-left:4px solid #F59E0B; color:#ddd;'><b>📝 Instructions</b></div>\
                    <div style='flex:1; background:#2a2a2a; padding:10px; border-left:4px solid #EC4899; color:#ddd;'><b>🎯 Practice</b></div>\
                </div>")
            }),
            ("Quality / Monitoring", {
                "classes": ("tab", "quality"),
                "fields": (
                    "enable_gold_units",
                    "gold_injection_frequency",
                    ("min_accuracy_required", "min_gold_before_eval"),
                    "gold_units_file",
                ),
                "description": mark_safe(f"{notice_html}<div style='background:#1e293b; padding:15px; border-left:4px solid #8b5cf6; color:#e2e8f0; border-radius:4px; margin-top:20px;'>\
                    <b>🤖 MACE Analysis</b> available in Actions menu.\
                </div>")
            }),
            ("Distribution", {
                "classes": ("tab", "distribution"),
                "fields": (
                    "prolific_completion_code",
                    "distribution_strategy",
                    ("min_annotations_per_doc", "max_annotations_per_doc"),
                    ("block_size", "annotators_per_block"),
                    "prioritize_unannotated"
                ),
                "description": mark_safe(f"{notice_html}<p style='margin-top:10px;'>Configure document serving and Prolific redirection.</p>")
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

    def _render_config_block(self, obj, config_data, title, icon):
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

    @admin.display(description="")
    def status_notice(self, obj):
        if not obj or not obj.pk:
            return ""
            
        if obj.is_published:
            clone_url = reverse('admin:project_quick_clone', args=[obj.pk])
            return format_html(
                '''
                <div style="background: rgba(245, 158, 11, 0.15); border: 2px solid #f59e0b; border-radius: 12px; padding: 20px; margin-bottom: 5px; display: flex; align-items: center; justify-content: space-between; gap: 16px; width: 100%;">
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <span style="font-size: 32px;">🔒</span>
                        <div style="line-height: 1.5;">
                            <div style="font-weight: 900; color: #f59e0b; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px;">Progetto Lanciato & Bloccato</div>
                            <div style="color: #94a3b8; font-size: 13.5px; font-weight: 500;">La configurazione è sigillata per garantire la validità scientifica. Per modificare i parametri, è necessario creare una copia.</div>
                        </div>
                    </div>
                    <button type="button" onclick="quickCloneProject(this, '{}', '{}', true)" style="background: #f59e0b; color: white; padding: 10px 20px; border-radius: 10px; font-weight: 800; border:none; cursor:pointer; font-size: 13px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); transition: transform 0.1s;" onmousedown="this.style.transform='scale(0.95)'" onmouseup="this.style.transform='scale(1)'">📋 CLONA E MODIFICA</button>
                </div>
                ''',
                clone_url, obj.name
            )
        elif obj.status == 'LIVE':
            draft_url = reverse('admin:project_set_status', args=[obj.pk])
            return format_html(
                '''
                <div style="background: rgba(59, 130, 246, 0.15); border: 2px solid #3b82f6; border-radius: 12px; padding: 20px; margin-bottom: 5px; display: flex; align-items: center; justify-content: space-between; gap: 16px; width: 100%;">
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <span style="font-size: 32px;">▶️</span>
                        <div style="line-height: 1.5;">
                            <div style="font-weight: 900; color: #3b82f6; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px;">Playground Attivo (LIVE)</div>
                            <div style="color: #94a3b8; font-size: 13.5px; font-weight: 500;">Il progetto è in fase di test. I campi sono in sola lettura per evitare conflitti; torna in DRAFT per apportare modifiche.</div>
                        </div>
                    </div>
                    <button type="button" onclick="quickUpdateStatus(this, '{}', 'DRAFT', 'Draft')" style="background: #3b82f6; color: white; padding: 10px 20px; border-radius: 10px; font-weight: 800; border:none; cursor:pointer; font-size: 13px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); transition: transform 0.1s;" onmousedown="this.style.transform='scale(0.95)'" onmouseup="this.style.transform='scale(1)'">📁 TORNA IN DRAFT</button>
                </div>
                ''',
                draft_url
            )
        return ""

    @admin.display(description="Task Config")
    def formatted_task_type_config(self, obj):
        return self._render_config_block(obj, obj.task_type_config, 'Task Configuration', '⚙️')

    @admin.display(description="Screening Config")
    def formatted_screening_config(self, obj):
        return self._render_config_block(obj, obj.screening_config, 'Screening Configuration', '📋')

    def _render_markdown_block(self, obj, md_text, title, icon):
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
        processed = []
        for line in text.split('\n'):
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
            '  <div class="config-header" style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(128,128,128,0.1); color: #64748b;">'
            '    <div style="display: flex; align-items: center; gap: 8px;">'
            '      <span class="config-icon">{icon}</span> <strong style="font-size: 13px;">{title}</strong>'
            '    </div>'
            '    <div style="display: flex; gap: 6px;">'
            '        <button type="button" class="copy-json-btn" onclick="copyMarkdownToClipboard(this)" '
            '                style="background: rgba(48,110,232,0.1); color: #306ee8; border: none; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.2s;"'
            '                onmouseover="this.style.background=\'rgba(48,110,232,0.2)\'" onmouseout="this.style.background=\'rgba(48,110,232,0.1)\'">'
            '           📋 Copy Markdown'
            '        </button>'
            '    </div>'
            '  </div>'
            '  <div class="markdown-raw-content" style="display: none;">{raw_md}</div>'
            '  <div style="font-family: \'Outfit\', \'Inter\', sans-serif; font-size: 13px; line-height: 1.7; color: inherit;">{content}</div>'
            '</div>',
            icon=icon,
            title=title,
            content=mark_safe(text),
            raw_md=md_text
        )

    @admin.display(description="Codebook Content")
    def formatted_codebook_content(self, obj):
        return self._render_markdown_block(obj, obj.codebook_content, 'Codebook Materials', '📖')

    @admin.display(description="Instructions Content")
    def formatted_instructions_content(self, obj):
        return self._render_markdown_block(obj, obj.instructions_content, 'Task Instructions', '📝')

    @admin.display(description="Practice Task Config")
    def formatted_practice_task_config(self, obj):
        return self._render_config_block(obj, obj.practice_task_config, 'Practice Task', '🎯')

    def get_urls(self):
        urls = super(ProjectAdmin, self).get_urls()
        my_urls = [
            path(
                '<path:object_id>/export/', 
                self.admin_site.admin_view(self.download_export_view), 
                name='project_export_jsonl'
            ),
            path(
                '<path:object_id>/set-status/',
                self.admin_site.admin_view(self.set_status_view),
                name='project_set_status'
            ),
            path(
                '<path:object_id>/nuke-data/',
                self.admin_site.admin_view(self.nuke_project_view),
                name='project_nuke_data'
            ),
            path(
                '<path:object_id>/launch-data/',
                self.admin_site.admin_view(self.launch_project_view),
                name='project_launch_data'
            ),
            path(
                '<path:object_id>/quick-clone/',
                self.admin_site.admin_view(self.clone_project_view),
                name='project_quick_clone'
            ),
            path(
                '<path:object_id>/run-mace/',
                self.admin_site.admin_view(self.run_mace_view),
                name='project_run_mace'
            ),
        ]
        return my_urls + urls

    def set_status_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            project, message = ProjectService.set_project_status(object_id, new_status, user=request.user)
            return JsonResponse({'status': 'success', 'new_status': project.status, 'message': message})
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') and len(e.messages) > 0 else str(e)
            return JsonResponse({'status': 'error', 'message': str(msg)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def nuke_project_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
        try:
            message = ProjectService.nuke_project_data(object_id, user=request.user)
            return JsonResponse({'status': 'success', 'message': message})
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def launch_project_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
        try:
            message = ProjectService.launch_project(object_id, user=request.user)
            return JsonResponse({'status': 'success', 'message': message})
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            return JsonResponse({'status': 'error', 'message': str(msg)}, status=400)
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def clone_project_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
        try:
            data = json.loads(request.body)
            clone_mode = data.get('clone_mode')
            new_name = data.get('new_name')
            if not clone_mode:
                clone_dataset = data.get('clone_dataset', False)
                clone_mode = 'full' if clone_dataset else 'config'
            
            project, message = ProjectService.clone_project(
                object_id, 
                clone_mode=clone_mode, 
                user=request.user,
                new_name=new_name
            )
            return JsonResponse({'status': 'success', 'message': message})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def run_mace_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
        try:
            result = run_mace_for_project(object_id)
            if result.get("status") == "success":
                return JsonResponse({'status': 'success', 'message': result['message']})
            else:
                return JsonResponse({'status': 'error', 'message': result.get('message', 'MACE Error')}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def download_export_view(self, request, object_id):
        project = self.get_object(request, object_id)
        response = HttpResponse(content_type='application/x-jsonlines')
        filename = f"{project.name.replace(' ', '_').lower()}_annotations.jsonl"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        annotations = Annotation.objects.filter(
            document__project=project,
            document__is_gold_unit=False
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
            <button type="button" 
               onclick="quickExportProject(this, '{}', '{}')"
               class="bg-primary-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-primary-700 transition inline-block whitespace-nowrap text-center cursor-pointer border-none"
               title="Download .jsonl">
               ⬇ JSONL
            </button>
            ''',
            url, obj.name
        )

    @admin.display(description="Status & Operations", ordering='status')
    def status_badge(self, obj):
        status_colors = {
            'DRAFT': ('#64748b', '📁'), 
            'LIVE': ('#10b981', '▶️'),   
            'PAUSED': ('#f59e0b', '⏸️'), 
            'COMPLETED': ('#3b82f6', '✅'), 
        }
        bg_color, icon = status_colors.get(obj.status, ('#64748b', '❓'))
        buttons_html = ""
        for val, label in Project.STATUS_CHOICES:
            if val == obj.status: continue
            if obj.is_published and val == 'DRAFT': continue
            _, btn_icon = status_colors.get(val, ('#64748b', str(val[0])))
            update_url = reverse('admin:project_set_status', args=[obj.pk])
            buttons_html += f'''
                <button type="button" 
                        onclick="quickUpdateStatus(this, '{update_url}', '{val}', '{label}')"
                        title="Change to {label}"
                        class="status-panel-custom-btn">
                    <span>{btn_icon}</span> <span class="truncate">{label}</span>
                </button>
            '''
        actions_panel = ""
        if not obj.is_published:
            nuke_url = reverse('admin:project_nuke_data', args=[obj.pk])
            launch_url = reverse('admin:project_launch_data', args=[obj.pk])
            clone_url = reverse('admin:project_quick_clone', args=[obj.pk])
            actions_panel = f'''
                <div class="mt-4">
                    <button type="button" onclick="quickLaunchProject(this, '{launch_url}')" title="Lock project and Launch it to Production" class="launch-official-btn">🚀 LAUNCH OFFICIAL</button>
                    <button type="button" onclick="quickNukeProject(this, '{nuke_url}')" title="Delete all practice annotations" class="nuke-test-data-btn">🗑️ Nuke Test Data</button>
                    <button type="button" onclick="quickCloneProject(this, \'{clone_url}\', \'{obj.name}\', false)" title="Clone this project" class="clone-project-btn">📋 Clone Project</button>
                    <button type="button" onclick="quickRunMace(this, '{reverse('admin:project_run_mace', args=[obj.pk])}')" title="Calculate Annotator Reliability (MACE)" class="run-mace-btn">🤖 Run MACE Analysis</button>
                </div>
            '''
        else:
            clone_url = reverse('admin:project_quick_clone', args=[obj.pk])
            mace_url = reverse('admin:project_run_mace', args=[obj.pk])
            actions_panel = f'''
                <div class="mt-4 flex flex-col items-center gap-2">
                    <span class="officially-published-badge">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                        OFFICIALLY PUBLISHED
                    </span>
                    <button type="button" onclick="quickCloneProject(this, \'{clone_url}\', \'{obj.name}\', true)" title="Clone this project" class="clone-project-btn">📋 Edit/Clone Project</button>
                    <button type="button" onclick="quickRunMace(this, '{mace_url}')" title="Calculate Annotator Reliability (MACE)" class="run-mace-btn">🤖 Run MACE Analysis</button>
                </div>
            '''
        return mark_safe(
            f'<div class="status-badge-container flex flex-col w-[200px] max-w-[250px]">'
            f'  <div class="flex items-center justify-between mb-3">'
            f'      <span class="text-[11px] font-semibold opacity-60 uppercase">Current State</span>'
            f'      <span class="status-indicator" style="background: {bg_color}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; display: flex; align-items: center; gap: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">'
            f'          {icon} {obj.status}'
            f'      </span>'
            f'  </div>'
            f'  <div class="text-[10px] opacity-50 mb-1.5 font-semibold">TRANSITION TO:</div>'
            f'  <div class="flex gap-1.5 w-full">'
            f'      {buttons_html}'
            f'  </div>'
            f'  {actions_panel}'
            f'</div>'
        )

    @admin.display(description="Documents")
    def documents_link(self, obj):
        count = obj.documents.filter(is_gold_unit=False).count()
        url = reverse("admin:annotation_documentproxy_changelist") + "?" + urlencode({"project__id": f"{obj.id}", "o": "1"})
        return format_html('<a href="{}" class="admin-doc-link" style="background:#4f46e5; color:white; padding:7px 14px; border-radius:10px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:6px; min-width:140px;" onmouseover="this.style.background=\'#4338ca\'" onmouseout="this.style.background=\'#4f46e5\'"><span style="font-size:14px;">📄</span> <span>({}) Documents</span></a>', url, count)

    @admin.display(description="Gold Units")
    def gold_units_link(self, obj):
        count = obj.documents.filter(is_gold_unit=True).count()
        url = reverse("admin:annotation_goldunitproxy_changelist") + "?" + urlencode({"project__id": f"{obj.id}", "o": "1"})
        return format_html('<a href="{}" class="admin-gold-link" style="background:#eab308; color:white; padding:7px 14px; border-radius:10px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:6px; min-width:140px;" onmouseover="this.style.background=\'#ca8a04\'" onmouseout="this.style.background=\'#eab308\'"><span style="font-size:14px;">🛡️</span> <span>({}) Gold Units</span></a>', url, count)

    @admin.display(description="Annotations", ordering='-created_at')
    def annotations_link(self, obj):
        count = Annotation.objects.filter(document__project=obj).count()
        url = reverse("admin:annotation_annotation_changelist") + "?" + urlencode({"document__project__id": f"{obj.id}", "o": "1", "category": "regular"})
        bg = "#10b981" if count > 0 else "#64748b"
        return format_html('<a href="{}" style="background:{}; color:white; padding:7px 14px; border-radius:10px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:6px; min-width:140px;" title="Manage Annotations"><span style="font-size:14px;">📊</span> <span>({}) Annotations</span></a>', url, bg, count)

    @admin.display(description="Workers")
    def enrollments_link(self, obj):
        count = obj.enrollments.count()
        url = reverse("admin:annotation_projectenrollment_changelist") + "?" + urlencode({"project__id": f"{obj.id}"})
        return format_html('<a href="{}" style="background:#8b5cf6; color:white; padding:6px 14px; border-radius:10px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:6px; min-width:140px;" title="Manage Workers"><span style="font-size:14px;">👥</span> <span>({}) Workers</span></a>', url, count)

    @admin.display(description="Participant Link & Preview")
    def link_prolific(self, obj):
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
        full_url = f"{base_url}/{obj.slug}?PROLIFIC_PID="
        input_id = f"preview_pid_{obj.pk}"
        is_pub_js = str(obj.is_published).lower()
        return format_html(
            '''
            <div style="display: flex; flex-direction: column; gap: 8px; min-width: 210px; padding: 4px;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <code style="background: rgba(0,0,0,0.3); padding: 5px 8px; border-radius: 6px; font-size: 10px; flex: 1; border: 1px solid rgba(255,255,255,0.1); color: #f8fafc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{}</code>
                    <button type="button" onclick="navigator.clipboard.writeText(\'{}\'); if(window.adminNotify) window.adminNotify(\'info\', \'Link\', \'Copied!\')" 
                            style="background: #334155; border: 1px solid #475569; padding: 4px 6px; border-radius: 6px; cursor: pointer; color: white; font-size: 10px;">📋</button>
                </div>
                <div style="display: flex; flex-direction: column; gap: 4px; background: rgba(255,255,255,0.03); padding: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                    <label style="font-size: 10px; font-weight: 700; color: #cbd5e1; text-transform: uppercase;">Simulation Prolific PID</label>
                    <div style="display: flex; gap: 4px;">
                        <input type="text" id="{}" value="ADMIN_TEST" style="flex: 1; padding: 6px 8px; border: 1px solid #475569; border-radius: 6px; font-size: 11px; background: #0f172a; color: white; outline: none;">
                        <button type="button" onclick="window.openProjectPreview(\'{}\', \'{}\', \'{}\', {})"
                                style="background: #3b82f6; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-weight: 700; font-size: 11px;">👁️ Test as Partecipant</button>
                    </div>
                </div>
            </div>
            ''',
            full_url, full_url, input_id, base_url, obj.slug, input_id, is_pub_js
        )

    def save_model(self, request, obj, form, change):
        is_new = not obj.pk
        old_status = None
        if not is_new:
            old_status = Project.objects.get(pk=obj.pk).status
        super(ProjectAdmin, self).save_model(request, obj, form, change)
        if is_new:
            ProjectLogEntry.objects.create(project=obj, action="Project Created", details=f"Project '{obj.name}' initialized.")
        elif old_status != obj.status:
            ProjectLogEntry.objects.create(project=obj, action="Status Changed", details=f"Status changed from {old_status} to {obj.status}.")

        # File uploads
        for field, handler in [('upload_task_config', parse_json_upload), ('upload_screening_config', parse_json_upload), ('upload_practice_task_config', parse_json_upload)]:
            f = form.cleaned_data.get(field)
            if f:
                setattr(obj, field.replace('upload_', ''), handler(f))
                obj.save()

        for field in ['upload_codebook_content', 'upload_instructions_content']:
            f = form.cleaned_data.get(field)
            if f:
                setattr(obj, field.replace('upload_', ''), f.read().decode('utf-8'))
                obj.save()

        if 'documents_file' in form.changed_data and obj.documents_file:
            process_uploaded_dataset(obj, obj.documents_file)
        if 'gold_units_file' in form.changed_data and obj.gold_units_file:
            process_uploaded_dataset(obj, obj.gold_units_file)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        return super().render_change_form(request, context, add, change, form_url, obj)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and (obj.is_published or obj.status == 'LIVE'):
            locked = ['name', 'slug', 'description', 'informed_consent_config', 'dataset_text_key', 'dataset_id_key', 'enable_screening', 'enable_codebook', 'enable_instructions', 'enable_practice_task', 'practice_task_required', 'enable_gold_units', 'gold_injection_frequency', 'min_accuracy_required', 'min_gold_before_eval', 'distribution_strategy', 'min_annotations_per_doc', 'max_annotations_per_doc', 'block_size', 'annotators_per_block', 'prioritize_unannotated', 'documents_file', 'gold_units_file', 'prolific_completion_code']
            for f in locked:
                if f not in readonly: readonly.append(f)
        return readonly
