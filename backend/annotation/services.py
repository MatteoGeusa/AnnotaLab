import json
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Document, Project, ProjectEnrollment, Annotation, ProjectLogEntry
from .gold_strategies import get_strategy, check_gold_correctness

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
        
        current_regular_docs_count = Document.objects.filter(project=project, is_gold_unit=False).count()
        regular_docs_added_in_this_batch = 0

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

                # Calculate block_id for SAME_ANNOTATORS strategy
                block_id = None
                if not is_gold_final and project.distribution_strategy == 'SAME_ANNOTATORS' and project.block_size > 0:
                    block_id = (current_regular_docs_count + regular_docs_added_in_this_batch) // project.block_size

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
                        'block_id': block_id,
                    }
                )
                if not is_gold_final:
                    regular_docs_added_in_this_batch += 1
                count += 1     
        except Exception as e:
            raise e
    
    return count, warnings

def parse_json_upload(file_obj):
    """
    Reads a Django UploadedFile (or InMemoryUploadedFile) and returns
    the parsed JSON content as a Python dict/list.
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

class ProjectService:
    @staticmethod
    def clone_project(project_id, clone_dataset=False, user=None):
        project = Project.objects.get(id=project_id)
        old_name = project.name
        
        with transaction.atomic():
            project.pk = None
            project.name = f"{old_name} (Clone)"
            project.slug = "" 
            project.status = 'DRAFT'
            project.is_published = False
            project.launched_at = None
            project.save()
            
            message = f"Project '{old_name}' cloned successfully."
            
            if clone_dataset:
                docs = Document.objects.filter(project_id=project_id)
                count = docs.count()
                new_docs = []
                for d in docs:
                    d.pk = None 
                    d.project = project
                    new_docs.append(d)
                Document.objects.bulk_create(new_docs, batch_size=500)
                message += f" {count} documents also cloned."

            ProjectLogEntry.objects.create(
                project=project,
                action="Project Cloned",
                details=f"Cloned from '{old_name}' (Dataset: {clone_dataset}) by {user.username if user else 'System'}."
            )
        return project, message

    @staticmethod
    def set_project_status(project_id, new_status, user=None):
        project = Project.objects.get(id=project_id)
        old_status = project.status
        if old_status == new_status:
            return project, "No change needed."

        # Validate LIVE transition
        if new_status == 'LIVE':
            has_docs = project.documents.filter(is_gold_unit=False).exists()
            if not has_docs:
                raise ValidationError("Cannot set to LIVE: No documents found in database.")

        project.status = new_status
        project.save(update_fields=['status'])
        
        ProjectLogEntry.objects.create(
            project=project,
            action="Status Updated (Quick)",
            details=f"Project status changed from {old_status} to {new_status} by {user.username if user else 'System'}."
        )
        return project, f"Status updated to {new_status}."

    @staticmethod
    def nuke_project_data(project_id, user=None):
        project = Project.objects.get(id=project_id)
        if project.status not in ['DRAFT', 'PAUSED']:
            raise ValueError("Project must be in DRAFT or PAUSED state to Nuke data.")
        
        with transaction.atomic():
            annotation_count = Annotation.objects.filter(document__project=project).delete()[0]
            enrollment_count = ProjectEnrollment.objects.filter(project=project).delete()[0]
            
            msg = f"Deleted {annotation_count} annotations and {enrollment_count} workers."
            ProjectLogEntry.objects.create(
                project=project,
                action="Data Nuked ☢️",
                details=f"{msg} by {user.username if user else 'System'}."
            )
        return msg

    @staticmethod
    def launch_project(project_id, user=None):
        project = Project.objects.get(id=project_id)
        if project.is_published:
            raise ValueError("Project is already launched.")

        with transaction.atomic():
            # Nuke existing data before launch
            annotation_count = Annotation.objects.filter(document__project=project).delete()[0]
            enrollment_count = ProjectEnrollment.objects.filter(project=project).delete()[0]
            
            # Transition safely
            project.is_published = True
            project.status = 'LIVE'
            project.launched_at = timezone.now()
            project.save() # Triggers model validation

            # Safety check
            has_docs = project.documents.filter(is_gold_unit=False).exists()
            if not has_docs:
                raise ValueError("Cannot Launch: No documents found in database.")

            msg = f"Cleaned {annotation_count} annotations, {enrollment_count} workers. Project officially Launched!"
            ProjectLogEntry.objects.create(
                project=project,
                action="Project Launched 🚀",
                details=f"{msg} Action by {user.username if user else 'System'}."
            )
        return msg

class DistributionService:
    @staticmethod
    def get_next_task(project, annotator, enrollment):
        """Logic to determine the next task for an annotator."""
        if enrollment.exclude_from_distribution:
            return {"status": "stopped", "message": "Access denied for this project."}

        if enrollment.status == 'EXCLUDED':
            return {"status": "stopped", "message": "You have been excluded from this project due to quality issues."}
        
        if enrollment.status == 'COMPLETED':
            return {"status": "completed"}

        if enrollment.status == 'PENDING':
            return {"status": "stopped", "message": "Please complete all pre-task steps first."}

        # Current progress count
        done_count = annotator.annotations.filter(document__project=project).count()
        
        with transaction.atomic():
            target_id = DistributionService._get_candidate_id(project, annotator, enrollment, done_count)
            
            if not target_id:
                if enrollment.status != 'COMPLETED':
                    enrollment.status = 'COMPLETED'
                    enrollment.save(update_fields=['status'])
                return {"status": "completed"}

            # Lock the document for concurrency safety
            final_doc = Document.objects.select_for_update(skip_locked=True).filter(id=target_id).first()
            
            if not final_doc:
                # If locking failed, might need to retry or return completed if no more exist
                return {"status": "retry"} 

        return {"status": "ok", "document": final_doc}

    @staticmethod
    def _get_candidate_id(project, annotator, enrollment, done_count):
        # A. QUALITY CONTROL (GOLD INJECTION)
        if DistributionService._should_inject_gold(project, done_count):
             gold_id = DistributionService._find_gold_candidate(project, annotator)
             if gold_id:
                 return gold_id

        # B. REGULAR PHASE - NORMAL DOCUMENTS
        return DistributionService._find_normal_candidate(project, annotator, enrollment)

    @staticmethod
    def _should_inject_gold(project, done_count):
        if not project.enable_gold_units:
            return False
        injection_freq = project.gold_injection_frequency or 0
        return injection_freq > 0 and (done_count + 1) % injection_freq == 0

    @staticmethod
    def _find_gold_candidate(project, annotator):
        return Document.objects.filter(
            project=project,
            is_gold_unit=True
        ).exclude(
            annotations__annotator=annotator
        ).values_list('id', flat=True).first()

    @staticmethod
    def _find_normal_candidate(project, annotator, enrollment):
        from django.db.models import Count
        base_qs = Document.objects.filter(project=project, is_gold_unit=False)
        
        if project.distribution_strategy == 'SAME_ANNOTATORS':
            if enrollment.assigned_block_id is None:
                max_capacity = project.annotators_per_block
                existing_blocks = Document.objects.filter(
                    project=project, 
                    is_gold_unit=False, 
                    block_id__isnull=False
                ).values_list('block_id', flat=True).distinct().order_by('block_id')
                
                assigned = False
                for block in existing_blocks:
                    enrolled_in_block = ProjectEnrollment.objects.filter(project=project, assigned_block_id=block).count()
                    if enrolled_in_block < max_capacity:
                        enrollment.assigned_block_id = block
                        enrollment.save(update_fields=['assigned_block_id'])
                        assigned = True
                        break
                if not assigned: return None

            base_qs = base_qs.filter(block_id=enrollment.assigned_block_id)

        base_qs = base_qs.exclude(annotations__annotator=annotator).annotate(num_anns=Count('annotations'))
        
        if project.distribution_strategy in ['STANDARD', 'SAME_ANNOTATORS']:
            candidates = base_qs.filter(num_anns__lt=project.max_annotations_per_doc)
            order = 'num_anns' if project.prioritize_unannotated else '?'
            candidates = candidates.order_by(order)
        else: # FULL_OVERLAP
            candidates = base_qs.order_by('?')
        
        return candidates.values_list('id', flat=True).first()
