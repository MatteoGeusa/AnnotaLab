import json
from ..models import Document

def process_uploaded_dataset(project, file_obj):
    """
    DATASET IMPORT LOGIC (Dynamic Keys Version)
    Legge un file JSONL usando le chiavi configurate nel Progetto.
    """
    count = 0
    file_obj.open() 
    file_obj.seek(0)

    # Recuperiamo le chiavi configurate dall'utente
    text_key = project.dataset_text_key
    id_key = project.dataset_id_key

    try:
        # Usiamo enumerate per avere il numero di riga (idx) che parte da 1
        for idx, line in enumerate(file_obj, start=1):
            try:
                line_str = line.decode('utf-8').strip()
            except AttributeError:
                line_str = line.strip()
            
            if not line_str: continue 

            try:
                data = json.loads(line_str)
            except json.JSONDecodeError:
                continue
            
            # 1. CERCA IL TESTO (Necessario)
            text = data.get(text_key)

            # 2. CERCA L'ID (Opzionale / Configurabile)
            # Se la chiave c'è nel config E c'è nel JSON -> Usa quella
            if id_key and id_key in data:
                external_id = str(data.get(id_key))
            else:
                # Altrimenti -> Usa il seriale (numero di riga)
                # Aggiungiamo un prefisso per evitare collisioni banali
                external_id = f"row_{idx}"

            # Fallback testo (se la chiave esiste ma il valore è vuoto)
            if not text:
                text = f"[CONTENT REDACTED]\nID: {external_id}"
            
            # Opzionale: Prova a recuperare metadati extra se esistono
            subreddit = data.get('subreddit', 'unknown')

            # Creazione Documento
            obj, created = Document.objects.get_or_create(
                project=project,
                external_id=external_id,
                defaults={
                    'text': text,
                    'metadata': {'subreddit': subreddit, 'original_row': idx},
                    'min_annotations_required': project.min_annotations_per_doc
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

class HighlightMedia:
    css = {
        'all': ('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/stackoverflow-light.min.css',)
    }
    js = (
        'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js',
        'js/admin_highlight_init.js',
    )
