import json
from .models import Document

def process_uploaded_dataset(project, file_obj, is_gold=False):
    """
    DATASET IMPORT LOGIC
    Reads a JSONL file and imports documents.
    
    :param is_gold: If True, all documents in this file are treated as gold units.
    """
    count = 0
    warnings = []

    # Extract valid classification values from the project's task config
    task_config = project.task_type_config or {}
    valid_class_values = {
        label.get('value') 
        for label in task_config.get('class_labels', []) 
        if label.get('value')
    }

    with file_obj.open() as f:
        text_key = project.dataset_text_key
        id_key = project.dataset_id_key

        try:
            for idx, line in enumerate(f, start=1):
                try:
                    line_str = line.decode('utf-8').strip()
                except AttributeError:
                    line_str = line.strip()
                
                if not line_str: continue 

                try:
                    data = json.loads(line_str)
                except json.JSONDecodeError:
                    warnings.append(f"Row {idx}: Invalid JSON, skipped.")
                    continue
                
                text = data.get(text_key)
                if id_key and id_key in data:
                    external_id = str(data.get(id_key))
                else:
                    external_id = str(idx)

                # Identify solution if it's a gold file
                gold_sol = data.get('gold_solution', None)
                is_gold_final = is_gold # Strictly follow the file type

                # DYNAMIC METADATA
                # Special keys that are not metadata
                special_keys = {text_key, id_key, 'is_gold_unit', 'gold_solution'}
                metadata = {k: v for k, v in data.items() if k not in special_keys}

                if not text:
                    text = f"[CONTENT REDACTED]\nID: {external_id}"

                # VALIDATE GOLD UNIT CONSISTENCY
                if is_gold_final:
                    if not gold_sol or not isinstance(gold_sol, dict):
                        warnings.append(
                            f"Row {idx}: Gold unit is missing 'gold_solution' or it's not a dict. "
                            f"Skipped because this file is for Gold Units only."
                        )
                        continue
                    elif valid_class_values:
                        gold_class = gold_sol.get('classification')
                        if gold_class and gold_class not in valid_class_values:
                            warnings.append(
                                f"Row {idx}: Gold solution classification '{gold_class}' "
                                f"is not in project's class_labels {sorted(valid_class_values)}. "
                                f"Skipped."
                            )
                            continue
                        elif not gold_class:
                           warnings.append(f"Row {idx}: Gold solution is missing 'classification' key. Skipped.")
                           continue

                # Upsert Document (Update if exists, Create if new)
                # We identify a document uniquely by (Project + External ID)
                obj, created = Document.objects.update_or_create(
                    project=project,
                    external_id=external_id,
                    defaults={
                        'text': text,
                        'metadata': metadata,
                        'is_gold_unit': is_gold_final, 
                        'gold_solution': gold_sol if is_gold_final else None,
                        'min_annotations_required': project.min_annotations_per_doc,
                    }
                )
                count += 1     
        except Exception as e:
            raise e
    
    return count, warnings

def parse_json_upload(file_obj):
    """
    Reads a Django UploadedFile (or InMemoryUploadedFile) and returns
    the parsed JSON content as a Python dict/list.
    Raises ValueError on invalid JSON.
    """
    content = file_obj.read()
    try:
        text = content.decode('utf-8')
    except AttributeError:
        text = content
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
