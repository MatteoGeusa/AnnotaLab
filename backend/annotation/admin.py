from django.contrib import admin
from django.db.models import Count
from .models import Project, Document, Annotator, Annotation
from import_export import resources
from import_export.admin import ImportExportModelAdmin
import json
from django.contrib import messages
from django.http import HttpResponse
from unfold.admin import ModelAdmin

def process_uploaded_dataset(project, file_obj):
    """
    DATASET IMPORT LOGIC / LOGICA IMPORTAZIONE DATASET
    ---------------------------------------------------------
    EN: Reads a standard JSONL file line by line and converts it into Document objects.
        - Supports fallback for text encoding issues.
        - Creates a default 'redacted' text if actual text is missing.
        - Idempotent: uses get_or_create to avoid duplicates based on External ID.
    
    IT: Legge un file JSONL riga per riga e lo converte in oggetti Documento.
        - Gestisce fallback per problemi di encoding.
        - Crea un testo 'redacted' di default se manca il testo reale.
        - Idempotente: usa get_or_create per evitare duplicati basandosi sull'External ID.
    """
    count = 0
    
    file_obj.open() 
    file_obj.seek(0)

    try:
        for line in file_obj:
            try:
                line_str = line.decode('utf-8').strip()
            except AttributeError:
                # Fallback in case the file is already open as text
                line_str = line.strip()
            
            if not line_str: 
                continue 
            try:
                data = json.loads(line_str)
            except json.JSONDecodeError:
                continue
            
            external_id = data.get('_id')
            text = data.get('text')
            subreddit = data.get('subreddit')

            # Fallback testo
            if not text:
                text = f"[CONTENT REDACTED]\nID: {external_id}"

            # Document Creation
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

@admin.action(description='Export Annotations (PsyCoMark JSONL Format)')
def export_annotations_jsonl(modeladmin, request, queryset):
    """
    DATA EXPORT LOGIC / LOGICA ESPORTAZIONE DATI
    ---------------------------------------------------------
    EN: Generates the final dataset for machine learning training.
        - Iterates efficiently using 'select_related' to minimize DB hits.
        - Normalizes span offsets to be explicitly character-based (startIndex, endIndex).
        - Maps internal labels (e.g., 'Actor') to the output schema types.
    
    IT: Genera il dataset finale per il training del machine learning.
        - Itera efficientemente usando 'select_related' per minimizzare query al DB.
        - Normalizza gli offset degli span per essere esplicitamente basati sui caratteri.
        - Mappa le etichette interne (es. 'Actor') sui tipi dello schema di output.
    """
    # Set response as downloadable file
    response = HttpResponse(content_type='application/x-jsonlines')
    response['Content-Disposition'] = 'attachment; filename="psycomark_annotations.jsonl"'

    # Iterate over selected projects (usually one)
    for project in queryset:
        # Retrieve all annotations linked to this project
        # Use select_related to avoid thousands of DB queries (optimization)
        annotations = Annotation.objects.filter(document__project=project).select_related('document', 'annotator')

        for ann in annotations:
            # 1. Retrieve raw data saved by Frontend
            raw_result = ann.result # { "classification": "Yes", "spans": [...] }
            
            # 2. Transform SPANS into the required format
            # Frontend uses: start, end, label
            # Output requires: startIndex, endIndex, type
            formatted_markers = []
            raw_spans = raw_result.get('spans', [])
            
            if isinstance(raw_spans, list):
                for span in raw_spans:
                    formatted_markers.append({
                        "startIndex": span.get('start'),
                        "endIndex": span.get('end'),
                        "type": span.get('label'),       # Map 'label' to 'type'
                        "text": span.get('text')
                    })

            # 3. Build the final object
            output_obj = {
                "_id": ann.document.external_id,
                "conspiracy": raw_result.get('classification'),
                "markers": formatted_markers,
                "subreddit": ann.document.metadata.get('subreddit', 'unknown'),
                "annotator": ann.annotator.prolific_pid
            }

            # 4. Write the line to the file
            response.write(json.dumps(output_obj) + '\n')

    return response

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ('name', 'created_at', 'doc_count')
    actions = [export_annotations_jsonl]

    def save_model(self, request, obj, form, change):
        # 1. Save file to disk first
        super().save_model(request, obj, form, change)
        
        # 2. Check if there is a new file
        if 'dataset_file' in form.changed_data and obj.dataset_file:
            try:
                print("New dataset file detected. Starting processing...")
                count = process_uploaded_dataset(obj, obj.dataset_file)
                messages.success(request, f"Import successful! Created {count} documents.")
            except Exception as e:
                messages.error(request, f"Import error: {str(e)}")

    @admin.display(description="Num Documents")
    def doc_count(self, obj):
        return obj.documents.count()

class DocumentResource(resources.ModelResource):
    class Meta:
        model = Document
        # Here we specify which CSV columns to read
        fields = ('id', 'text', 'external_id', 'project')

# 2. DOCUMENT Configuration
@admin.register(Document)
class DocumentAdmin(ImportExportModelAdmin):
    resource_class = DocumentResource
    list_display = ('id', 'short_text', 'project', 'current_annotations_count', 'is_completed')
    list_filter = ('project', 'min_annotations_required') # Useful side filters!
    search_fields = ('text', 'external_id')               # Search in text or original ID
    
    # To avoid showing kilometer-long texts in the list, we truncate them
    @admin.display(description="Text Preview")
    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    # A visual column (True/False) to see if it's finished
    @admin.display(boolean=True, description="Completed?")
    def is_completed(self, obj):
        return obj.current_annotations_count >= obj.min_annotations_required

# 3. ANNOTATOR Configuration
@admin.register(Annotator)
class AnnotatorAdmin(ModelAdmin):
    list_display = ('prolific_pid', 'created_at', 'annotations_made')
    search_fields = ('prolific_pid',)

    @admin.display(description="Tasks Performed")
    def annotations_made(self, obj):
        return obj.annotations.count()

# 4. ANNOTATION Configuration (Results)
@admin.register(Annotation)
class AnnotationAdmin(ModelAdmin):
    list_display = ('id', 'document', 'annotator', 'created_at')
    list_filter = ('document__project',) # Filter annotations by Batch
    readonly_fields = ('created_at',)    # Avoid accidental date edits