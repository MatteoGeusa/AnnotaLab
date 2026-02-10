from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from django.http import HttpResponse
from django.contrib import messages
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin, TabularInline
import json
from django.urls import path
from .models import Project, Document, Annotator, Annotation

# 1. HELPER FUNCTIONS (Import Logic)

def process_uploaded_dataset(project, file_obj):
    count = 0
    file_obj.open() 
    file_obj.seek(0)

    try:
        for line in file_obj:
            try:
                line_str = line.decode('utf-8').strip()
            except AttributeError:
                line_str = line.strip()
            
            if not line_str: continue 

            try:
                data = json.loads(line_str)
            except json.JSONDecodeError:
                continue
            
            external_id = data.get('_id')
            text = data.get('text')
            subreddit = data.get('subreddit')

            if not text:
                text = f"[CONTENT REDACTED]\nID: {external_id}"

            obj, created = Document.objects.get_or_create(
                project=project,
                external_id=external_id,
                defaults={
                    'text': text,
                    'metadata': {'subreddit': subreddit},
                    'min_annotations_required': 3
                }
            )
            if created:
                count += 1     
    except Exception as e:
        raise e
    
    return count

def process_uploaded_config(project, file_obj):
    file_obj.open()
    file_obj.seek(0)
    try:
        content = file_obj.read()
        try:
            json_content = content.decode('utf-8')
        except AttributeError:
            json_content = content
            
        config_data = json.loads(json_content)
        project.configuration = config_data
        project.save()
        return True
    except Exception as e:
        raise e

# 3. ADMIN CONFIGURATION

class AnnotationInline(TabularInline):
    model = Annotation
    extra = 0
    readonly_fields = ('created_at', 'annotator', 'result','milliseconds_to_complete')
    can_delete = False
    show_change_link = True
    verbose_name = "Received Annotation"
    verbose_name_plural = "Annotations on this Document"

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    # 1. AGGIUNTO 'export_list_button' QUI SOTTO
    list_display = ('name', 'created_at', 'documents_link', 'annotations_link', 'export_list_button')
    
    # Usiamo 'export_detail_button' per coerenza con la definizione sotto
    readonly_fields = ('configuration', 'export_detail_button')
    
    fieldsets = (
        ("General Information", {
            "fields": ("name", "description")
        }),
        ("Configuration", {
            "fields": ("configuration_file", "configuration"),
            "description": "Upload a JSON file to overwrite the configuration displayed below."
        }),
        ("Dataset & Distribution", {
            "fields": (
                "dataset_file", 
                "distribution_strategy",
                ("min_annotations_per_doc", "max_annotations_per_doc"),
                "prioritize_unannotated"
            )
        }),
        ("Data Export", {
            "fields": ("export_detail_button",), # Usa il bottone grande qui
            "description": "Scarica tutte le annotazioni raccolte per questo progetto."
        }),
    )

    # --- CUSTOM URLS & VIEW ---
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

    # --- BOTTONI ---

    # BOTTONE 1: Lista (Piccolo)
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

    # BOTTONE 2: Dettaglio (Grande)
    @admin.display(description="Export Data")
    def export_detail_button(self, obj):
        url = reverse('admin:project_export_jsonl', args=[obj.pk])
        return format_html(
            '''
            <a href="{}" class="bg-primary-600 text-white px-4 py-2 rounded-md font-bold hover:bg-primary-700 transition" style="display:inline-block; text-decoration:none;">
                ⬇️ Download Annotations (.jsonl)
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

class DocumentResource(resources.ModelResource):
    class Meta:
        model = Document
        fields = ('id', 'text', 'external_id', 'project')

@admin.register(Document)
class DocumentAdmin(ImportExportModelAdmin):
    resource_class = DocumentResource
    list_display = ('external_id', 'short_text', 'project', 'current_annotations_count', 'is_gold_unit', 'is_completed')
    list_filter = ('project', 'is_gold_unit', 'min_annotations_required')
    search_fields = ('text', 'external_id', 'metadata')
    
    inlines = [AnnotationInline]

    fieldsets = (
        ("Document Content", {
            "fields": (
                "external_id",  
                "text",         
            ),
            "description": "The main content that will be shown to annotators."
        }),
        ("Context & Metadata", {
            "fields": (
                "project",
                "metadata",     
            ),
        }),
        ("Annotation Strategy", {
            "fields": (
                ("min_annotations_required", "is_gold_unit"),       
            ),
            "description": "Define if this is a quality control test (Gold Unit) or a standard document."
        }),
    )

    @admin.display(description="Text Preview")
    def short_text(self, obj):
        return obj.text[:80] + "..." if len(obj.text) > 80 else obj.text

    @admin.display(boolean=True, description="Completed?")
    def is_completed(self, obj):
        return obj.current_annotations_count >= obj.min_annotations_required
    

@admin.register(Annotator)
class AnnotatorAdmin(ModelAdmin):
    list_display = ('prolific_pid', 'created_at', 'view_work_link')
    search_fields = ('prolific_pid',)

    @admin.display(description="History")
    def view_work_link(self, obj):
        count = obj.annotations.count()
        url = (
            reverse("admin:annotation_annotation_changelist")
            + "?"
            + urlencode({"annotator__id": f"{obj.id}"})
        )
        return format_html('<a href="{}" style="font-weight:bold;">View {} Tasks</a>', url, count)


@admin.register(Annotation)
class AnnotationAdmin(ModelAdmin):
    list_display = ('id', 'document_link', 'annotator_link', 'created_at', 'milliseconds_to_complete')
    list_filter = ('document__project',) 
    readonly_fields = ('created_at',)
    
    @admin.display(description="Document")
    def document_link(self, obj):
        return obj.document.external_id

    @admin.display(description="Annotator")
    def annotator_link(self, obj):
        return obj.annotator.prolific_pid