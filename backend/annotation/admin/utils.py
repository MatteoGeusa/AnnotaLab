import json
from ..models import Document

def process_uploaded_dataset(project, file_obj):
    """
    DATASET IMPORT LOGIC (Dynamic Keys Version)
    Reads a JSONL file using the keys configured in the Project.
    Returns a tuple: (created_count, warnings_list)
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

    # Use context manager to ensure file is closed properly (Fix for Windows file locking)
    with file_obj.open() as f:
        # Get the user-configured keys
        text_key = project.dataset_text_key
        id_key = project.dataset_id_key

        try:
            # Use enumerate to track the row number (idx) starting at 1
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
                
                # 1. FIND THE TEXT (Required)
                text = data.get(text_key)

                # 2. FIND THE ID (Optional / Configurable)
                # If the key exists in the config AND in the JSON -> Use it
                if id_key and id_key in data:
                    external_id = str(data.get(id_key))
                else:
                    # Otherwise -> Use row number as a serial ID
                    # Add a prefix to avoid trivial collisions
                    external_id = f"row_{idx}"

                # Fallback text (if the key exists but the value is empty)
                if not text:
                    text = f"[CONTENT REDACTED]\nID: {external_id}"
                
                # Optional: try to retrieve extra metadata if it exists
                subreddit = data.get('subreddit', 'unknown')
                
                # GOLD UNIT + SOLUTION
                is_gold = data.get('is_gold_unit', False)
                gold_sol = data.get('gold_solution', None)

                # VALIDATE GOLD UNIT CONSISTENCY
                if is_gold:
                    if not gold_sol or not isinstance(gold_sol, dict):
                        warnings.append(
                            f"Row {idx}: Gold unit is missing 'gold_solution' or it's not a dict. "
                            f"Imported as regular document."
                        )
                        is_gold = False
                        gold_sol = None
                    elif valid_class_values:
                        gold_class = gold_sol.get('classification')
                        if gold_class and gold_class not in valid_class_values:
                            warnings.append(
                                f"Row {idx}: Gold solution classification '{gold_class}' "
                                f"is not in project's class_labels {sorted(valid_class_values)}. "
                                f"Imported as regular document."
                            )
                            is_gold = False
                            gold_sol = None
                        elif not gold_class:
                            warnings.append(
                                f"Row {idx}: Gold solution is missing 'classification' key. "
                                f"Imported as regular document."
                            )
                            is_gold = False
                            gold_sol = None

                # Create Document
                obj, created = Document.objects.get_or_create(
                    project=project,
                    external_id=external_id,
                    defaults={
                        'text': text,
                        'metadata': {'subreddit': subreddit, 'original_row': idx},
                        'min_annotations_required': project.min_annotations_per_doc,
                        'is_gold_unit': is_gold,
                        'gold_solution': gold_sol
                    }
                )
                if created:
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

class HighlightMedia:
    css = {
        'all': ('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/stackoverflow-light.min.css',)
    }
    js = (
        'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js',
        'js/admin_highlight_init.js',
    )