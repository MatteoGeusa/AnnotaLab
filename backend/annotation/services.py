import json
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Document, Project, ProjectEnrollment, Annotation, ProjectLogEntry
from .gold_strategies import get_strategy, check_gold_correctness
from .schema_validator import validate_annotation_schema, validate_gold_solution

def process_uploaded_dataset(project, file_obj):
    """
    DATASET IMPORT LOGIC
    Reads a JSONL file and imports documents.
    """
    count = 0
    warnings = []

    schema = project.annotation_schema or {}

    with transaction.atomic():
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

                    # VALIDATE GOLD UNIT AGAINST ANNOTATION SCHEMA
                    if is_gold_final:
                        errs, warns = validate_gold_solution(gold_sol, schema)
                        for w in warns:
                            warnings.append(f"Row {idx} (note): {w}")
                        if errs:
                            for e in errs:
                                warnings.append(f"Row {idx} (skipped): {e}")
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

def parse_yaml_upload(file_obj, validate_as_schema=False):
    """
    Reads a Django UploadedFile and returns the parsed content as a Python
    dict/list. Accepts both YAML and JSON files (JSON is valid YAML).

    If validate_as_schema=True, the parsed content is validated as an
    annotation_schema.  A ValueError is raised with a human-readable
    error summary if validation fails.
    """
    import yaml
    content = file_obj.read()
    try:
        text = content.decode('utf-8')
    except AttributeError:
        text = content

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML/JSON: {e}")

    if validate_as_schema:
        errors = validate_annotation_schema(data)
        if errors:
            raise ValueError(
                "Annotation schema validation failed:\n" +
                "\n".join(f"  • {e}" for e in errors)
            )

    return data

# Backward-compatibility alias
parse_json_upload = parse_yaml_upload

class ProjectService:
    @staticmethod
    def clone_project(project_id, clone_mode='config', user=None, new_name=None):
        """
        Clones a project with different modes:
        - 'config': Settings only.
        - 'full': Settings + All documents (Regular & Gold).
        - 'incomplete': Settings + Unannotated documents + Active Workers.
        """
        source_project = Project.objects.get(id=project_id)
        old_name = source_project.name
        
        if not new_name:
            new_name = f"{old_name} (Clone)"
            
        with transaction.atomic():
            # Clone project object (settings)
            new_project = Project.objects.get(id=project_id)
            new_project.pk = None
            new_project.name = new_name
            new_project.slug = ""  # Let save() generate a new slug from name
            new_project.status = 'DRAFT'
            new_project.is_published = False
            new_project.launched_at = None
            
            # Handle slug uniqueness if the generated slug already exists
            from django.utils.text import slugify
            base_slug = slugify(new_name)
            if not base_slug:
                base_slug = "cloned-project"
                
            unique_slug = base_slug
            counter = 1
            while Project.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            
            new_project.slug = unique_slug
            new_project.save()
            
            message = f"Project '{old_name}' cloned successfully."
            
            # 1. Handle Document Cloning
            docs_qs = Document.objects.filter(project_id=project_id)
            
            if clone_mode == 'full':
                # Already have the full queryset
                pass
            elif clone_mode == 'incomplete':
                # Clone Gold Units + Incomplete Documents
                from django.db.models import Q
                docs_qs = docs_qs.filter(
                    Q(is_gold_unit=True) | 
                    Q(current_annotations_count__lt=source_project.min_annotations_per_doc)
                )
            elif clone_mode == 'config':
                docs_qs = Document.objects.none()
            else: # Fallback for backward compatibility (clone_dataset=True/False)
                if clone_mode is True or clone_mode == 'true':
                    clone_mode = 'full'
                else:
                    docs_qs = Document.objects.none()

            if docs_qs.exists():
                count = docs_qs.count()
                new_docs = []
                for d in docs_qs:
                    d.pk = None 
                    d.project = new_project
                    d.current_annotations_count = 0 
                    new_docs.append(d)
                Document.objects.bulk_create(new_docs, batch_size=500)
                message += f" {count} documents also cloned."

            # 2. Handle Enrollment Cloning (Only for 'incomplete' mode)
            if clone_mode == 'incomplete':
                enrollments = ProjectEnrollment.objects.filter(project_id=project_id).exclude(status__in=['COMPLETED', 'EXCLUDED'])
                if enrollments.exists():
                    e_count = enrollments.count()
                    new_enrollments = []
                    for e in enrollments:
                        e.pk = None
                        e.project = new_project
                        # Reset quality metrics for fresh start in new project
                        e.gold_tasks_completed = 0
                        e.gold_accuracy = None
                        e.gold_strikes = 0
                        # Keep existing status if it was active/pending
                        new_enrollments.append(e)
                    ProjectEnrollment.objects.bulk_create(new_enrollments)
                    message += f" {e_count} active workers also migrated."

            ProjectLogEntry.objects.create(
                project=new_project,
                action="Project Cloned",
                details=f"Cloned from '{old_name}' (Mode: {clone_mode}) by {user.username if user else 'System'}."
            )

            # Ensure the owner is always a ProjectMembership record on the new project
            if user:
                from .models import ProjectMembership
                ProjectMembership.objects.get_or_create(
                    project=new_project,
                    user=new_project.owner,
                    defaults={'role': 'OWNER'},
                )
        return new_project, message

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
            # Safety check BEFORE mutating state
            has_docs = project.documents.filter(is_gold_unit=False).exists()
            if not has_docs:
                raise ValueError("Cannot Launch: No documents found in database.")

            # Nuke existing data before launch
            annotation_count = Annotation.objects.filter(document__project=project).delete()[0]
            enrollment_count = ProjectEnrollment.objects.filter(project=project).delete()[0]
            
            # Transition safely
            project.is_published = True
            project.status = 'LIVE'
            project.launched_at = timezone.now()
            project.save()  # Triggers model validation

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
        import random
        
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

        # Optimization: fast ID exclusion instead of JOIN on the annotations table
        done_ids = annotator.annotations.filter(document__project=project).values_list('document_id', flat=True)
        base_qs = base_qs.exclude(id__in=done_ids)
        
        if project.distribution_strategy in ['STANDARD', 'SAME_ANNOTATORS']:
            candidates = base_qs.filter(current_annotations_count__lt=project.max_annotations_per_doc)
            if project.prioritize_unannotated:
                return candidates.order_by('current_annotations_count').values_list('id', flat=True).first()
            else:
                # Optimization: avoid order_by('?') on the DB. Slice and randomly pick in Python
                valid_ids = list(candidates.values_list('id', flat=True)[:100])
                return random.choice(valid_ids) if valid_ids else None
        else: # FULL_OVERLAP
            valid_ids = list(base_qs.values_list('id', flat=True)[:100])
            return random.choice(valid_ids) if valid_ids else None
