from django.contrib import admin
from django.db.models import Count
from .models import Project, Document, Annotator, Annotation
from import_export import resources
from import_export.admin import ImportExportModelAdmin
import json
from django.contrib import messages
from django.http import HttpResponse

def process_uploaded_dataset(project, file_obj):
    """
    Legge il file caricato e crea i Documenti.
    """
    print(f"--- INIZIO IMPORTAZIONE PER: {project.name} ---")
    count = 0
    
    # 1. APERTURA SICURA
    # Apriamo il file
    file_obj.open() 
    
    # 2. RIAVVOLGIMENTO (IL FIX FONDAMENTALE)
    # Assicuriamoci di essere all'inizio del file
    file_obj.seek(0)

    try:
        for line in file_obj:
            # 3. DECODIFICA
            # I file caricati sono bytes, dobbiamo farli diventare stringhe
            try:
                line_str = line.decode('utf-8').strip()
            except AttributeError:
                # Fallback nel caso il file sia già aperto come testo
                line_str = line.strip()
            
            if not line_str: 
                continue 

            # Parsing JSON
            try:
                data = json.loads(line_str)
            except json.JSONDecodeError:
                print(f"Riga ignorata (JSON non valido): {line_str[:50]}...")
                continue
            
            external_id = data.get('_id')
            text = data.get('text')
            subreddit = data.get('subreddit')

            # Fallback testo
            if not text:
                text = f"[CONTENT REDACTED]\nID: {external_id}"

            # Creazione Documento
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
        print(f"ERRORE GRAVE DURANTE LETTURA: {e}")
        raise e
    
    print(f"--- FINE IMPORTAZIONE: Creati {count} documenti ---")
    return count

@admin.action(description='Esporta Annotazioni (Format PsyCoMark JSONL)')
def export_annotations_jsonl(modeladmin, request, queryset):
    """
    Genera un file .jsonl scaricabile con tutte le annotazioni dei progetti selezionati.
    Formatta i dati esattamente come richiesto (startIndex, type, ecc.)
    """
    # Impostiamo la risposta come file scaricabile
    response = HttpResponse(content_type='application/x-jsonlines')
    response['Content-Disposition'] = 'attachment; filename="psycomark_annotations.jsonl"'

    # Iteriamo sui progetti selezionati (solitamente uno)
    for project in queryset:
        # Recuperiamo tutte le annotazioni collegate a questo progetto
        # Usiamo select_related per evitare migliaia di query al DB (ottimizzazione)
        annotations = Annotation.objects.filter(document__project=project).select_related('document', 'annotator')

        for ann in annotations:
            # 1. Recuperiamo i dati grezzi salvati dal Frontend
            raw_result = ann.result # { "classification": "Yes", "spans": [...] }
            
            # 2. Trasformiamo gli SPAN nel formato richiesto
            # Frontend usa: start, end, label
            # Output richiede: startIndex, endIndex, type
            formatted_markers = []
            raw_spans = raw_result.get('spans', [])
            
            if isinstance(raw_spans, list):
                for span in raw_spans:
                    formatted_markers.append({
                        "startIndex": span.get('start'),
                        "endIndex": span.get('end'),
                        "type": span.get('label'),       # Mappiamo 'label' su 'type'
                        "text": span.get('text')
                    })

            # 3. Costruiamo l'oggetto finale
            output_obj = {
                "_id": ann.document.external_id,
                "conspiracy": raw_result.get('classification'),
                "markers": formatted_markers,
                "subreddit": ann.document.metadata.get('subreddit', 'unknown'),
                "annotator": ann.annotator.prolific_pid
            }

            # 4. Scriviamo la riga nel file
            response.write(json.dumps(output_obj) + '\n')

    return response

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'doc_count')
    actions = [export_annotations_jsonl]

    def save_model(self, request, obj, form, change):
        # 1. Salviamo prima il file su disco
        super().save_model(request, obj, form, change)
        
        # 2. Controlliamo se c'è un file nuovo
        if 'dataset_file' in form.changed_data and obj.dataset_file:
            try:
                print("Rilevato nuovo file dataset. Avvio processamento...")
                count = process_uploaded_dataset(obj, obj.dataset_file)
                messages.success(request, f"Importazione riuscita! Creati {count} documenti.")
            except Exception as e:
                messages.error(request, f"Errore importazione: {str(e)}")

    @admin.display(description="N. Documenti")
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
class AnnotatorAdmin(admin.ModelAdmin):
    list_display = ('prolific_pid', 'created_at', 'annotations_made')
    search_fields = ('prolific_pid',)

    @admin.display(description="Tasks Performed")
    def annotations_made(self, obj):
        return obj.annotations.count()

# 4. ANNOTATION Configuration (Results)
@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'annotator', 'created_at')
    list_filter = ('document__project',) # Filter annotations by Batch
    readonly_fields = ('created_at',)    # Avoid accidental date edits