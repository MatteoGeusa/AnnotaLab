from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.http import urlencode
from django.http import HttpResponse
from django.contrib import messages
import json
from ..models import Project, Annotation
from .utils import process_task_config, process_screening_config, process_uploaded_dataset

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    # Aggiungi i nuovi campi a list_display se vuoi vederli subito
    list_display = ('name', 'created_at', 'documents_link', 'annotations_link', 'export_list_button')
    
    readonly_fields = ('formatted_task_type_config', 'formatted_screening_config',)
    
    fieldsets = (
        ("General Information", {
            "fields": ("name", "description", "informed_consent_config",)
        }),

        ("Configuration", {
            "fields": (
                
                ("configuration_task_type_file", "configuration_screening_file"),
                ("formatted_task_type_config", "formatted_screening_config"),
               
            ),
            "description": """
               Upload specific JSON files to overwrite the project configuration.<br><br>
               <b>1. Task Configuration File:</b>
               <ul style="margin-left: 20px; list-style-type: disc; margin-bottom: 5px;">
                   <li><b>Purpose:</b> Defines the task interface and logic.</li>
                   <li><b>Keys:</b> <code>task_type</code>, <code>class_labels</code>, <code>span_labels</code>, <code>gold_injection_frequency</code>.</li>
               </ul>
               <b>2. Screening Configuration File:</b>
               <ul style="margin-left: 20px; list-style-type: disc;">
                   <li><b>Purpose:</b> Defines the screening/training logic.</li>
                   <li><b>Keys:</b> <code>min_accuracy_required</code>, <code>training_tasks_required</code>.</li>
               </ul>
               <div style="background: #2a2a2a; padding: 10px; border-left: 4px solid #FFB700; color: #ddd;">
                <b>💡 Golden Units injection frequency:</b><br>
                The frequency of golden units injection is determined by the <code>gold_injection_frequency</code> key in the task configuration file.<br>
                The value of this key is the number of regular units to be annotated between two golden units.<br>
                For example, if the value is 5, a golden unit will be injected every 5 regular units.
                </div>
            """
        }),
  
        ("Input Data Mapping", {
            "fields": (
                ("dataset_text_key", "dataset_id_key"), # Sulla stessa riga
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
                    During the training/screening phase, user responses are automatically compared with the full <code>gold_solution</code>.
                </div>
            """
        }),

        ("Distribution Strategy", {
            "fields": (
                "distribution_strategy",
                ("min_annotations_per_doc", "max_annotations_per_doc"),
                "prioritize_unannotated"
            )
        })
    )


    @admin.display(description="Current Task Config (JSON)")
    def formatted_task_type_config(self, obj):
        # Se il campo è vuoto, mostra un trattino
        if not obj.task_type_config:
            return "-"
        
        json_str = json.dumps(obj.task_type_config, indent=4, sort_keys=True)
        
        return format_html(
            '''
            <pre style="background-color: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 12px; overflow-x: auto; max-height: 500px; border: 1px solid #333;"><code>{}</code></pre>
            ''',
            json_str
        )

    @admin.display(description="Current Screening Config (JSON)")
    def formatted_screening_config(self, obj):
        # Se il campo è vuoto, mostra un trattino
        if not obj.screening_config:
            return "-"
        
        json_str = json.dumps(obj.screening_config, indent=4, sort_keys=True)
        
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


    @admin.display(description="Documents")
    def documents_link(self, obj):
        count = obj.documents.count()
        url = (
            reverse("admin:annotation_document_changelist")
            + "?"
            + urlencode({"project__id": f"{obj.id}"})
        )
        return format_html(
            '''
            <a href="{}" 
               class="bg-blue-600 text-white px-3 py-1 rounded text-xs font-bold hover:bg-blue-700 transition inline-block text-center min-w-[100px]"
               title="View Documents">
               🔗 View {} Documents
            </a>
            ''',
            url, count
        )

    @admin.display(description="Result", ordering='-created_at')
    def annotations_link(self, obj):
        count = Annotation.objects.filter(document__project=obj).count()
        url = (
            reverse("admin:annotation_annotation_changelist")
            + "?"
            + urlencode({"document__project__id": f"{obj.id}"})
        )
        
        bg_class = "bg-green-600 hover:bg-green-700" if count > 0 else "bg-gray-400 hover:bg-gray-500"
        
        return format_html(
            '''
            <a href="{}" 
               class="{} text-white px-3 py-1 rounded text-xs font-bold transition inline-block text-center min-w-[100px]"
               title="View Annotations">
               🔗 View {} Annotations
            </a>
            ''',
            url, bg_class, count
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'configuration_task_type_file' in form.changed_data and obj.configuration_task_type_file:
            try:
                process_task_config(obj, obj.configuration_task_type_file)
                messages.success(request, "Task Configuration updated from JSON file!")
            except Exception as e:
                messages.error(request, f"Task Config Error: {str(e)}")
        
        if 'configuration_screening_file' in form.changed_data and obj.configuration_screening_file:
            try:
                process_screening_config(obj, obj.configuration_screening_file)
                messages.success(request, "Screening Configuration updated from JSON file!")
            except Exception as e:
                messages.error(request, f"Screening Config Error: {str(e)}")
        if 'dataset_file' in form.changed_data and obj.dataset_file:
            try:
                count = process_uploaded_dataset(obj, obj.dataset_file)
                messages.success(request, f"Import successful! Created {count} documents.")
            except Exception as e:
                messages.error(request, f"Import error: {str(e)}")
