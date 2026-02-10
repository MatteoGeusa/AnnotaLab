from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.http import urlencode
from django.http import HttpResponse
from django.contrib import messages
import json
from ..models import Project, Annotation
from .utils import process_uploaded_config, process_uploaded_dataset

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    # Aggiungi i nuovi campi a list_display se vuoi vederli subito
    list_display = ('name', 'created_at', 'documents_link', 'annotations_link', 'export_list_button')
    
    readonly_fields = ('formatted_configuration',)
    
    fieldsets = (
        ("General Information", {
            "fields": ("name", "description")
        }),

        ("Configuration", {
            "fields": ("configuration_file", "formatted_configuration"),
            "description": "Upload a JSON file to overwrite the configuration displayed below."
        }),
  
        ("Input Data Mapping", {
            "fields": (
                ("dataset_text_key", "dataset_id_key"), # Sulla stessa riga
                "dataset_file", 
            ),
            "description": "define which JSON keys to read from the file. If the ID is missing, the row number will be used."
        }),

        ("Distribution Strategy", {
            "fields": (
                "distribution_strategy",
                ("min_annotations_per_doc", "max_annotations_per_doc"),
                "prioritize_unannotated"
            )
        })
    )

    @admin.display(description="Current Configuration (JSON)")
    def formatted_configuration(self, obj):
        # Se il campo è vuoto, mostra un trattino
        if not obj.configuration:
            return "-"
        
        json_str = json.dumps(obj.configuration, indent=4, sort_keys=True)
        
        return format_html(
            '''
            <pre style="background-color: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 12px; overflow-x: auto; max-height: 500px; border: 1px solid #333;"><code>{}</code></pre>
            ''',
            json_str
        )

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

        annotations = Annotation.objects.filter(document__project=project).select_related('document', 'annotator')

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

    # --- LINKS ---
    @admin.display(description="Documents")
    def documents_link(self, obj):
        count = obj.documents.count()
        url = (
            reverse("admin:annotation_document_changelist")
            + "?"
            + urlencode({"project__id": f"{obj.id}"})
        )
        return format_html('<a href="{}" style="font-weight:bold; color:#007bff;">View {} Docs</a>', url, count)

    @admin.display(description="Total Annotations")
    def annotations_link(self, obj):
        count = Annotation.objects.filter(document__project=obj).count()
        url = (
            reverse("admin:annotation_annotation_changelist")
            + "?"
            + urlencode({"document__project__id": f"{obj.id}"})
        )
        color = "green" if count > 0 else "gray"
        return format_html('<a href="{}" style="color:{};">View {} Anns</a>', url, color, count)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'configuration_file' in form.changed_data and obj.configuration_file:
            try:
                process_uploaded_config(obj, obj.configuration_file)
                messages.success(request, "Configuration updated from JSON file!")
            except Exception as e:
                messages.error(request, f"Config Error: {str(e)}")
        if 'dataset_file' in form.changed_data and obj.dataset_file:
            try:
                count = process_uploaded_dataset(obj, obj.dataset_file)
                messages.success(request, f"Import successful! Created {count} documents.")
            except Exception as e:
                messages.error(request, f"Import error: {str(e)}")
