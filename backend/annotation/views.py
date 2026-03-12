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

        if not project.is_active:
            return Response({"error": "Project is not active"}, status=404)

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
            annotator=annotator,
            defaults={'target_tasks': project.target_tasks_per_annotator}
        )

        # Determine current step based on pipeline progression
        # Pipeline: CONSENT -> SCREENING -> CODEBOOK -> ONBOARDING -> ANNOTATION -> COMPLETED
        current_step = 'CONSENT'
        if annotator.consent_accepted:
            # Check if project has a survey and annotator hasn't completed it
            has_screening = project.enable_screening and project.screening_config and len(project.screening_config) > 0
            if has_screening and not annotator.screening_completed:
                current_step = 'SCREENING'
            elif project.enable_codebook and not enrollment.codebook_completed:
                current_step = 'CODEBOOK'
            elif project.enable_instructions and not annotator.onboarding_completed:
                current_step = 'INSTRUCTIONS'
            else:
                current_step = 'ONBOARDING'
        if annotator.onboarding_completed:
            current_step = 'ANNOTATION'
            
        # Check if already completed FOR THIS PROJECT
        done_count = Annotation.objects.filter(document__project=project, annotator=annotator).count()
        if done_count >= enrollment.target_tasks:
            current_step = 'COMPLETED'

        return Response({
            "status": "ok",
            "step": current_step,
            "completion_url": PROLIFIC_COMPLETION_URL if current_step == 'COMPLETED' else None
        })

class AcceptConsent(APIView):
    """ Saves that the user accepted the consent """
    def post(self, request):
        pid = request.data.get('pid')
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        annotator.consent_accepted = True
        annotator.save()
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
        
        if not project.is_active:
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
            annotator=annotator,
            defaults={'target_tasks': project.target_tasks_per_annotator}
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
        
        if not project.is_active:
            return Response({"error": "Project is not active"}, status=404)
        
        if not project.enable_instructions:
            return Response({"content": "", "skip": True})

        practice = project.practice_task_config or {}
        has_practice = bool(practice and practice.get('text'))

        return Response({
            "content": project.instructions_content or "",
            "practice_task": practice if has_practice else None,
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
        
        if not project.is_active:
            return Response({"error": "Project is not active"}, status=404)
        
        if annotator.screening_completed:
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
        annotator.screening_completed = True
        annotator.save()

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
        annotator.onboarding_completed = True
        annotator.save()
        
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
                annotator=annotator,
                defaults={'target_tasks': project.target_tasks_per_annotator}
            )
            
            # Check all pre-task phases
            screening_ok = annotator.screening_completed or not project.enable_screening or not project.screening_config or len(project.screening_config) == 0
            all_phases_complete = (
                annotator.consent_accepted and 
                screening_ok and 
                annotator.onboarding_completed
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
                        
                        # Get the configured evaluation strategy
                        gold_cfg = project.gold_config or {}
                        strategy_name = gold_cfg.get('evaluation_strategy', 'percentage')
                        strategy = get_strategy(strategy_name)
                        
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

        if not project.is_active:
            return Response({"status": "stopped", "message": "This project is currently not accepting annotations."})

        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project, 
            annotator=annotator,
            defaults={'target_tasks': project.target_tasks_per_annotator}
        )

        if enrollment.exclude_from_distribution:
            return Response({"status": "stopped", "message": "Access denied for this project."})

        # Check enrollment status
        if enrollment.status == 'EXCLUDED':
            return Response({"status": "stopped", "message": "You have been excluded from this project due to quality issues."})
        
        if enrollment.status == 'COMPLETED':
            return self._completed_response()

        # Check user progress for THIS project
        done_count = annotator.annotations.filter(document__project=project).count()
        if done_count >= enrollment.target_tasks:
            enrollment.status = 'COMPLETED'
            enrollment.save()
            return self._completed_response()
        
        if enrollment.status == 'PENDING':
            # User hasn't completed pre-task phases yet
            return Response({"status": "stopped", "message": "Please complete all pre-task steps first."})

        # TASK SELECTION (Concurrency Safe)
        with transaction.atomic():
            target_id = self._get_candidate_id(project, annotator, enrollment, done_count)
            
            if not target_id:
                return self._completed_response()

            final_doc = Document.objects.select_for_update(skip_locked=True).filter(id=target_id).first()

        if final_doc:
            return self._task_response(final_doc, enrollment)
        
        return self._completed_response()

    def _get_candidate_id(self, project, annotator, enrollment, done_count):
        """ Internal logic to find the 'next' candidate ID """
        
        # A. QUALITY CONTROL (GOLD INJECTION)
        if self._should_inject_gold(project, done_count):
             gold_id = self._find_gold_candidate(project, annotator)
             if gold_id:
                 return gold_id

        # B. REGULAR PHASE - NORMAL DOCUMENTS
        return self._find_normal_candidate(project, annotator)

    def _should_inject_gold(self, project, done_count):
        """ Determines if a Gold Unit should be injected based on frequency settings """
        gold_cfg = project.gold_config or {}
        injection_freq = gold_cfg.get('gold_injection_frequency', 0)
        if not project.enable_gold_units:
            return False
        return injection_freq > 0 and (done_count + 1) % injection_freq == 0

    def _find_gold_candidate(self, project, annotator):
        """ Finds a Gold Unit the annotator hasn't seen yet """
        return Document.objects.filter(
            project=project,
            is_gold_unit=True
        ).exclude(
            annotations__annotator=annotator
        ).values_list('id', flat=True).first()

    def _find_normal_candidate(self, project, annotator):
        """ Finds a regular document based on the distribution strategy """
        base_qs = Document.objects.filter(
            project=project,
            is_gold_unit=False
        ).exclude(
            annotations__annotator=annotator
        ).annotate(
            num_anns=Count('annotations')
        )

        candidates = base_qs
        
        if project.distribution_strategy == 'STANDARD':
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

    def _completed_response(self):
        """ Standard response when no more tasks are available or target is reached """
        return Response({
            "status": "completed", 
            "completion_url": PROLIFIC_COMPLETION_URL
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
        
        if not project.is_active:
            return Response({"error": "Project is not active"}, status=404)
        
        if annotator.consent_accepted:
            return Response({"error": "Already consented"}, status=400)

        return Response({
            "consent_text": project.informed_consent_config
        })