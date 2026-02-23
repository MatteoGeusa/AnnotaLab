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
    upload_screening_config = forms.FileField(
        required=False,
        label="Upload Screening Config (JSON)",
        help_text="Upload a JSON file to overwrite the Screening configuration."
    )

    class Meta:
        model = Project
        fields = '__all__'

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    # Columns visible in the project list view
    list_display = ('name', 'created_at', 'documents_link', 'enrollments_link', 'annotations_link', 'link_prolific','export_list_button')
    
    form = ProjectAdminForm
    readonly_fields = ('formatted_task_type_config', 'formatted_screening_config',)
    
    fieldsets = (
        ("General Information", {
            "fields": ("name", "description", "informed_consent_config",)
        }),

        ("Configuration", {
            "fields": (
                ("formatted_task_type_config", "formatted_screening_config"),
                ("upload_task_config", "upload_screening_config"),
            ),
            "description": """
                Live JSON configuration for this project. Upload a JSON file below to overwrite.<br>
                <div style="background: #2a2a2a; padding: 10px; border-left: 4px solid #FFB700; color: #ddd; margin-top: 8px;">
                <b>💡 Screening Configuration:</b><br>
                - <code>gold_injection_frequency</code>: Injects a gold unit every X regular units (e.g. 5).<br>
                - <code>continuous_screening</code> (bool): If true, users can be excluded if accuracy drops after screening.
                </div>
            """
        }),
  
        ("Input Data Mapping", {
            "fields": (
                ("dataset_text_key", "dataset_id_key"),
                "dataset_file", 
            ),
            "description": """
                Upload a <b>.jsonl</b> file where each line is a JSON object.<br><br>
                <b>Supported Fields:</b>
                <ul style="margin-left: 20px; list-style-type: disc; margin-bottom: 10px;">
                    <li><b>Text</b>: Key corresponding to 'Dataset text key' (default: <code>text</code>).</li>
                    <li><b>ID</b>: Key corresponding to 'Dataset id key' (default: <code>_id</code>).</li>
                    <li><b>is_gold_unit</b> (bool): If <code>true</code>, the document is a <b>Golden Unit</b>.</li>
                    <li><b>gold_solution</b> (json): The correct solution for quality control.</li>
                    <li><b>metadata</b> (json): Optional metadata. e.g. <code>{'subreddit': 'r/AskReddit',other_metadata: 'value'}</code></li>
                </ul>
                <div style="background: #2a2a2a; padding: 10px; border-left: 4px solid #FFB700; color: #ddd;">
                    <b>💡 Golden Units & Screening:</b><br>
                    <i>Golden Units</i> are the foundation of the Screening system. They are used to measure annotator reliability.
                    During the <b>gold task/screening phase</b>, user responses are automatically compared with the full <code>gold_solution</code>.
                </div>
            """
        }),

        ("Distribution Strategy", {
            "fields": (
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

        json_str = json.dumps(config_data, indent=4, sort_keys=True)
        colorized = self._colorize_json(json_str)

        return format_html(
            '<div class="json-config-display">'
            '  <div class="config-header">'
            '    <span class="config-icon">{icon}</span> {title}'
            '  </div>'
            '  <pre>{code}</pre>'
            '</div>',
            icon=icon,
            title=title,
            code=mark_safe(colorized)
        )

    @admin.display(description="Task Config")
    def formatted_task_type_config(self, obj):
        return self._render_config_block(obj.task_type_config, 'Task Configuration', '⚙️')

    @admin.display(description="Screening Config")
    def formatted_screening_config(self, obj):
        return self._render_config_block(obj.screening_config, 'Screening Configuration', '🛡️')

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
        count = obj.documents.count()
        url = (
            reverse("admin:annotation_document_changelist")
            + "?"
            + urlencode({"project__id": f"{obj.id}", "o": "1"})
        )
        return format_html(
            '''
            <a href="{}" 
               class="bg-blue-600 text-white px-3 py-1 rounded text-xs font-bold hover:bg-blue-700 transition inline-block text-center min-w-[120px]"
               title="Manage Documents">
               -> ({}) Manage Documents
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
        display_url = f"http://localhost:5173/?PROLIFIC_PID=&project_id={obj.id}"
        test_url = f"http://localhost:5173/?PROLIFIC_PID=TEST_USER_001&project_id={obj.id}"
        return format_html(
            '''
            <div style="display:flex; align-items:center; gap:8px; min-width:400px;">
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

        # --- Process uploaded Screening Config JSON ---
        screening_config_file = form.cleaned_data.get('upload_screening_config')
        if screening_config_file:
            try:
                obj.screening_config = parse_json_upload(screening_config_file)
                obj.save(update_fields=['screening_config'])
                messages.success(request, "Screening Configuration updated from JSON file!")
            except Exception as e:
                messages.error(request, f"Screening Config Error: {str(e)}")

        # --- Process uploaded Dataset JSONL ---
        if 'dataset_file' in form.changed_data and obj.dataset_file:
            try:
                count, import_warnings = process_uploaded_dataset(obj, obj.dataset_file)
                messages.success(request, f"Import successful! Created {count} documents.")
                for warn in import_warnings:
                    messages.warning(request, f"⚠️ {warn}")
            except Exception as e:
                messages.error(request, f"Import error: {str(e)}")
