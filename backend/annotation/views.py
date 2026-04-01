from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.conf import settings
from .models import Document, Annotator, Annotation, Project, ProjectEnrollment
from .serializers import DocumentSerializer, AnnotationSerializer
from .gold_strategies import get_strategy, check_gold_correctness
from django.db.models import Count

PROLIFIC_COMPLETION_URL = "https://app.prolific.co/submissions/complete?cc=TUO_CODICE_PROLIFIC"

class InitializeSession(APIView):
    """
    RETURNS USER STATE / RESTITUISCE STATO UTENTE
    ---------------------------------------------------------
    Determines which page the frontend should display based on the user's progress.
    Pipeline: CONSENT -> SCREENING -> ONBOARDING -> ANNOTATION -> COMPLETED
    """
    def post(self, request):
        pid = request.data.get('prolific_pid')
        project_id = request.data.get('project_id')
        project_slug = request.data.get('project_slug')

        if not pid:
            return Response({"error": "Missing PID"}, status=400)
        
        if not project_id and not project_slug:
            return Response({"error": "Missing Project ID or Slug"}, status=400)
            
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)

        if not project.can_accept_annotations:
            if project.status == 'DRAFT':
                return Response({"error": "This project is still in DRAF phase and not yet open."}, status=404)
            return Response({"error": f"Project is currently {project.status.lower()}"}, status=404)

        # Metadata extraction (e.g. STUDY_ID, SESSION_ID from Prolific)
        metadata = request.data.get('metadata', {})
        metadata.pop('project_id', None)
        metadata.pop('prolific_pid', None)
        metadata.pop('PROLIFIC_PID', None)
        
        annotator, created = Annotator.objects.get_or_create(prolific_pid=pid)
        
        if metadata:
            annotator.metadata.update(metadata)
            annotator.save()

        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project, 
            annotator=annotator
        )

        # Determine current step based on pipeline progression
        # Pipeline: CONSENT -> SCREENING -> CODEBOOK -> ONBOARDING -> ANNOTATION -> COMPLETED
        current_step = 'CONSENT'
        if enrollment.consent_accepted:
            # Check if project has a survey and annotator hasn't completed it
            has_screening = project.enable_screening and project.screening_config and len(project.screening_config) > 0
            if has_screening and not enrollment.screening_completed:
                current_step = 'SCREENING'
            elif project.enable_codebook and not enrollment.codebook_completed:
                current_step = 'CODEBOOK'
            elif (project.enable_instructions or project.enable_practice_task) and not enrollment.onboarding_completed:
                current_step = 'INSTRUCTIONS'
            else:
                current_step = 'ONBOARDING'
        if enrollment.onboarding_completed:
            current_step = 'ANNOTATION'
            
        # Fix state mismatch for global annotator completion flags vs local enrollment status
        if current_step == 'ANNOTATION' and enrollment.status == 'PENDING':
            enrollment.status = 'ACTIVE'
            enrollment.save(update_fields=['status'])
            
        # To check completion universally, rely on GetNextTask logic when it actually loads
        # Here we just assume they are annotating if in ANNOTATION phase, 
        # actual completion is detected when `GetNextTask` returns no more valid docs.
        # However, to avoid showing the 'ANNOTATION' loop indefinitely on refresh if there are literally 0 items,
        # we still flag 'COMPLETED' if `status` was set to completed by `GetNextTask`
        if enrollment.status == 'COMPLETED':
            current_step = 'COMPLETED'

        completion_url = PROLIFIC_COMPLETION_URL
        if project.prolific_completion_code:
            completion_url = f"https://app.prolific.co/submissions/complete?cc={project.prolific_completion_code}"

        return Response({
            "status": "ok",
            "step": current_step,
            "completion_url": completion_url if current_step == 'COMPLETED' else None
        })

class AcceptConsent(APIView):
    """ Saves that the user accepted the consent """
    def post(self, request):
        pid = request.data.get('pid')
        project_slug = request.data.get('project_slug')
        project_id = request.data.get('project_id')
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)
            
        enrollment, _ = ProjectEnrollment.objects.get_or_create(project=project, annotator=annotator)
        enrollment.consent_accepted = True
        enrollment.save()
        return Response({"status": "ok", "next_step": "SCREENING"})

class GetCodebook(APIView):
    """
    Returns the codebook content for a project.
    GET /api/v1/get-codebook/?pid=XX&project_slug=XX
    """
    def get(self, request):
        pid = request.query_params.get('pid')
        project_slug = request.query_params.get('project_slug')
        project_id = request.query_params.get('project_id')

        if not pid or (not project_id and not project_slug):
            return Response({"error": "Missing PID or Project identification"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        if not project.enable_codebook:
            return Response({"content": "", "skip": True})

        return Response({
            "content": project.codebook_content or "",
            "skip": False
        })

class CompleteCodebook(APIView):
    """
    Marks the codebook as completed for this annotator+project.
    POST /api/v1/codebook/
    Body: { pid, project_slug }
    """
    def post(self, request):
        pid = request.data.get('pid')
        project_slug = request.data.get('project_slug')
        project_id = request.data.get('project_id')

        if not pid:
            return Response({"error": "Missing PID"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        elif project_id:
            project = get_object_or_404(Project, id=project_id)
        else:
            return Response({"error": "Missing Project identification"}, status=400)
        
        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project,
            annotator=annotator
        )
        
        enrollment.codebook_completed = True
        enrollment.save()
        
        return Response({"status": "ok", "next_step": "INSTRUCTIONS"})

class GetInstructions(APIView):
    """
    Returns instructions content and practice task config for a project.
    GET /api/v1/get-instructions/?pid=XX&project_slug=XX
    """
    def get(self, request):
        pid = request.query_params.get('pid')
        project_slug = request.query_params.get('project_slug')
        project_id = request.query_params.get('project_id')

        if not pid or (not project_id and not project_slug):
            return Response({"error": "Missing PID or Project identification"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        if not project.enable_instructions and not project.enable_practice_task:
            return Response({"content": "", "skip": True})

        practice = project.practice_task_config or {}
        has_practice = bool(project.enable_practice_task and practice and practice.get('text'))

        # Use the dedicated admin boolean field as the source of truth
        practice_required = project.practice_task_required if has_practice else False

        return Response({
            "has_instructions": project.enable_instructions,
            "content": project.instructions_content or "",
            "practice_task": practice if has_practice else None,
            "practice_task_required": practice_required,
            "task_config": project.task_type_config or {},
            "skip": False
        })


class GetScreening(APIView):
    """
    Returns the screening questionnaire configuration for a project.
    GET /api/v1/get-screening/?pid=XX&project_slug=XX
    """
    def get(self, request):
        pid = request.query_params.get('pid')
        project_id = request.query_params.get('project_id')
        project_slug = request.query_params.get('project_slug')

        if not pid or (not project_id and not project_slug):
            return Response({"error": "Missing PID or Project identification"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        enrollment, _ = ProjectEnrollment.objects.get_or_create(project=project, annotator=annotator)
        
        if enrollment.screening_completed:
            return Response({"error": "Screening already completed"}, status=400)

        if not project.enable_screening:
            return Response({"questions": [], "skip": True})

        screening_config = project.screening_config or []
        
        if not screening_config:
            return Response({"questions": [], "skip": True})

        return Response({
            "questions": screening_config,
            "skip": False
        })

class SubmitScreening(APIView):
    """
    Saves screening responses from an annotator.
    POST /api/v1/screening/
    Body: { pid, project_slug, responses: { question_id: answer, ... } }
    """
    def post(self, request):
        pid = request.data.get('pid')
        project_slug = request.data.get('project_slug')
        project_id = request.data.get('project_id')
        responses = request.data.get('responses', {})

        if not pid:
            return Response({"error": "Missing PID"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        # Get project to validate required fields
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        elif project_id:
            project = get_object_or_404(Project, id=project_id)
        else:
            return Response({"error": "Missing Project identification"}, status=400)

        # Validate required fields
        screening_config = project.screening_config or []
        for question in screening_config:
            if question.get('required', False):
                q_id = question.get('id')
                if q_id not in responses or responses[q_id] is None or responses[q_id] == '':
                    return Response(
                        {"error": f"Required field '{question.get('label', q_id)}' is missing."},
                        status=400
                    )

        # Save responses into annotator metadata
        annotator.metadata['screening_responses'] = responses
        annotator.save()
        
        enrollment, _ = ProjectEnrollment.objects.get_or_create(project=project, annotator=annotator)
        enrollment.screening_completed = True
        enrollment.save()

        return Response({"status": "ok", "next_step": "ONBOARDING"})

class CompleteOnboarding(APIView):
    """ 
    Saves that the user completed instructions/training.
    Also transitions enrollment to ACTIVE if all pre-task phases are complete.
    """
    def post(self, request):
        pid = request.data.get('pid')
        project_slug = request.data.get('project_slug')
        project_id = request.data.get('project_id')
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        # Transition enrollment PENDING -> ACTIVE if all phases complete
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        elif project_id:
            project = get_object_or_404(Project, id=project_id)
        else:
            # Fallback: try to find any pending enrollment
            project = None

        if project:
            enrollment, _ = ProjectEnrollment.objects.get_or_create(
                project=project,
                annotator=annotator
            )
            
            enrollment.onboarding_completed = True
            
            # Check all pre-task phases
            screening_ok = enrollment.screening_completed or not project.enable_screening or not project.screening_config or len(project.screening_config) == 0
            all_phases_complete = (
                enrollment.consent_accepted and 
                screening_ok and 
                enrollment.onboarding_completed
            )
            
            if all_phases_complete and enrollment.status == 'PENDING':
                enrollment.status = 'ACTIVE'
            
            enrollment.save()

        return Response({"status": "ok", "next_step": "ANNOTATION"})

class SubmitAnnotation(APIView):
    """
    Endpoint: POST /api/v1/submit/
    Saves the user's work.
    """
    def post(self, request):
        pid = request.data.get('pid')
        if not pid:
            return Response({"error": "Missing PID"}, status=status.HTTP_400_BAD_REQUEST)
            
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        data = request.data.copy()
        serializer = AnnotationSerializer(data=data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    annotation = serializer.save(annotator=annotator)
                    
                    # --- QUALITY CONTROL / GOLD UNIT LOGIC ---
                    document = annotation.document
                    project = document.project
                    
                    enrollment, _ = ProjectEnrollment.objects.get_or_create(
                        project=project,
                        annotator=annotator
                    )
                    
                    if document.is_gold_unit:
                        enrollment.gold_tasks_completed += 1
                        
                        # Evaluate correctness using strategy pattern
                        annotation_result = data.get('result', {})
                        is_correct = check_gold_correctness(annotation_result, document.gold_solution)
                        
                        # Pack configuration into a dict for strategy compatibility (now hardcoded to percentage)
                        strategy = get_strategy()
                        gold_cfg = {
                            'min_accuracy_required': project.min_accuracy_required,
                            'min_gold_before_eval': project.min_gold_before_eval,
                        }
                        
                        # Execute strategy — updates enrollment fields internally
                        should_exclude, reason = strategy(enrollment, gold_cfg, is_correct)
                        
                        if should_exclude:
                            enrollment.status = 'EXCLUDED'
                        
                        enrollment.save()

                return Response({"status": "saved"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetNextTask(APIView):
    """
    DETERMINES THE NEXT TASK FOR THE ANNOTATOR
    ---------------------------------------------------------
    Logic:
    1. Check enrollment status (must be ACTIVE).
    2. Check if target tasks reached.
    3. Gold Injection logic OR Normal document selection.
    4. Concurrent safe selection using SKIP LOCKED.
    """
    def get(self, request):
        pid = request.query_params.get('pid')
        project_id = request.query_params.get('project_id')
        project_slug = request.query_params.get('project_slug')

        if not pid or (not project_id and not project_slug):
            return Response({"error": "Missing 'pid' or 'project' identification"}, status=400)

        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)

        if not project.can_accept_annotations:
            return Response({"status": "stopped", "message": f"This project is currently {project.status.lower()} and not accepting annotations."})

        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project, 
            annotator=annotator
        )

        if enrollment.exclude_from_distribution:
            return Response({"status": "stopped", "message": "Access denied for this project."})

        # Check enrollment status
        if enrollment.status == 'EXCLUDED':
            return Response({"status": "stopped", "message": "You have been excluded from this project due to quality issues."})
        
        if enrollment.status == 'COMPLETED':
            return self._completed_response(project)

        # Current count is still useful for gold injection frequency calculation
        done_count = annotator.annotations.filter(document__project=project).count()
        
        if enrollment.status == 'PENDING':
            # User hasn't completed pre-task phases yet
            return Response({"status": "stopped", "message": "Please complete all pre-task steps first."})

        # TASK SELECTION (Concurrency Safe)
        with transaction.atomic():
            target_id = self._get_candidate_id(project, annotator, enrollment, done_count)
            
            if not target_id:
                # No more candidates found meaning they actually completed everything
                if enrollment.status != 'COMPLETED':
                    enrollment.status = 'COMPLETED'
                    enrollment.save()
                return self._completed_response(project)

            final_doc = Document.objects.select_for_update(skip_locked=True).filter(id=target_id).first()

        if final_doc:
            return self._task_response(final_doc, enrollment)
        
        return self._completed_response(project)

    def _get_candidate_id(self, project, annotator, enrollment, done_count):
        """ Internal logic to find the 'next' candidate ID """
        
        # A. QUALITY CONTROL (GOLD INJECTION)
        if self._should_inject_gold(project, done_count):
             gold_id = self._find_gold_candidate(project, annotator)
             if gold_id:
                 return gold_id

        # B. REGULAR PHASE - NORMAL DOCUMENTS
        return self._find_normal_candidate(project, annotator, enrollment)

    def _should_inject_gold(self, project, done_count):
        """ Determines if a Gold Unit should be injected based on frequency settings """
        if not project.enable_gold_units:
            return False
        injection_freq = project.gold_injection_frequency or 0
        return injection_freq > 0 and (done_count + 1) % injection_freq == 0

    def _find_gold_candidate(self, project, annotator):
        """ Finds a Gold Unit the annotator hasn't seen yet """
        return Document.objects.filter(
            project=project,
            is_gold_unit=True
        ).exclude(
            annotations__annotator=annotator
        ).values_list('id', flat=True).first()

    def _find_normal_candidate(self, project, annotator, enrollment):
        """ Finds a regular document based on the distribution strategy """
        base_qs = Document.objects.filter(
            project=project,
            is_gold_unit=False
        )
        
        if project.distribution_strategy == 'SAME_ANNOTATORS':
            if enrollment.assigned_block_id is None:
                # Find the first available block with less than <max_capacity> active users
                max_capacity = project.annotators_per_block
                existing_blocks = Document.objects.filter(
                    project=project, 
                    is_gold_unit=False, 
                    block_id__isnull=False
                ).values_list('block_id', flat=True).distinct().order_by('block_id')
                
                assigned = False
                for block in existing_blocks:
                    enrolled_in_block = ProjectEnrollment.objects.filter(
                        project=project, 
                        assigned_block_id=block
                    ).count()
                    
                    if enrolled_in_block < max_capacity:
                        enrollment.assigned_block_id = block
                        enrollment.save(update_fields=['assigned_block_id'])
                        assigned = True
                        break
                
                if not assigned:
                     # No available blocks with space left -> return None
                     return None

            base_qs = base_qs.filter(block_id=enrollment.assigned_block_id)

        base_qs = base_qs.exclude(
            annotations__annotator=annotator
        ).annotate(
            num_anns=Count('annotations')
        )

        candidates = base_qs
        
        if project.distribution_strategy in ['STANDARD', 'SAME_ANNOTATORS']:
            candidates = candidates.filter(num_anns__lt=project.max_annotations_per_doc)
            order = 'num_anns' if project.prioritize_unannotated else '?'
            candidates = candidates.order_by(order)
            
        elif project.distribution_strategy == 'FULL_OVERLAP':
            candidates = candidates.order_by('?')
        
        return candidates.values_list('id', flat=True).first()

    def _task_response(self, doc, enrollment):
        """ Prepares the final Response JSON """
        serializer = DocumentSerializer(doc)
        data = serializer.data 
        
        data.update({
            'is_gold': doc.is_gold_unit,
            'feedback_enabled': False  # Gold feedback can be enabled per-project if needed
        })
            
        return Response(data)

    def _completed_response(self, project):
        """ Standard response when no more tasks are available or target is reached """
        code = project.prolific_completion_code
        url = f"https://app.prolific.com/submissions/complete?cc={code}" if code else PROLIFIC_COMPLETION_URL
        
        return Response({
            "status": "completed", 
            "completion_url": url
        })

class GetConsent(APIView):
    def get(self, request):
        pid = request.query_params.get('pid')
        project_id = request.query_params.get('project_id')
        project_slug = request.query_params.get('project_slug')

        if not pid or (not project_id and not project_slug):
            return Response({"error": "Missing PID or Project identification"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        enrollment, _ = ProjectEnrollment.objects.get_or_create(project=project, annotator=annotator)
        
        if enrollment.consent_accepted:
            return Response({"error": "Already consented"}, status=400)

        return Response({
            "consent_text": project.informed_consent_config
        })