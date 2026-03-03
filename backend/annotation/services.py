import json
from .models import Document

def process_uploaded_dataset(project, file_obj):
    """
    DATASET IMPORT LOGIC
    Reads a JSONL file and imports documents.
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
                # Identify solution
                gold_sol = data.get('gold_solution', None)
                # A document is a gold unit if and only if it has a gold_solution
                is_gold_final = bool(gold_sol and isinstance(gold_sol, dict))

                if id_key and id_key in data:
                    external_id = str(data.get(id_key))
                else:
                    # Prefix based on detected gold status
                    prefix = "G" if is_gold_final else "D"
                    external_id = f"{prefix}-{idx}"

                # DYNAMIC METADATA
                # Special keys that are not metadata
                special_keys = {text_key, id_key, 'is_gold_unit', 'gold_solution'}
                metadata = {k: v for k, v in data.items() if k not in special_keys}

                if not text:
                    text = f"[CONTENT REDACTED]\nID: {external_id}"

                # VALIDATE GOLD UNIT CONSISTENCY (ONLY IF DETECTED AS GOLD)
                if is_gold_final and valid_class_values:
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

                # Upsert Document
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
