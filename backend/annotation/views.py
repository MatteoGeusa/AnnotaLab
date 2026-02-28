from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.conf import settings
from .models import Document, Annotator, Annotation, Project, ProjectEnrollment
from .serializers import DocumentSerializer, AnnotationSerializer
from django.db.models import Count

PROLIFIC_COMPLETION_URL = "https://app.prolific.co/submissions/complete?cc=TUO_CODICE_PROLIFIC"

class InitializeSession(APIView):
    """
    RETURNS USER STATE / RESTITUISCE STATO UTENTE
    ---------------------------------------------------------
    EN: Determines which page the frontend should display based on the user's progress.
        Logic:
        1. If consent not accepted -> Show Consent Page.
        2. If consent accepted but onboarding incomplete -> Show Instructions.
        3. If onboarding complete -> Show Annotation Interface.
        4. If targets met -> Show Completion/Payment Code.

    IT: Determina quale pagina mostrare nel frontend in base al progresso dell'utente.
        Logica:
        1. Se consenso non accettato -> Mostra Pagina Consenso.
        2. Se consenso accettato ma onboarding incompleto -> Mostra Istruzioni.
        3. Se onboarding completo -> Mostra Interfaccia Annotazione.
        4. Se target raggiunti -> Mostra Completamento/Codice Pagamento.
    """
    def post(self, request):
        pid = request.data.get('prolific_pid')
        project_id = request.data.get('project_id')
        if not pid:
            return Response({"error": "Missing PID"}, status=400)
        
        # Check Project existence and status
        if not project_id:
            return Response({"error": "Missing Project ID"}, status=400)
            
        project = get_object_or_404(Project, id=project_id)
        if not project.is_active:
            return Response({"error": "Project is not active"}, status=404)

        # Metadata extraction (e.g. STUDY_ID, SESSION_ID from Prolific)
        metadata = request.data.get('metadata', {})
        # Remove redundant keys that are already handled by dedicated fields
        metadata.pop('project_id', None)
        metadata.pop('prolific_pid', None)
        metadata.pop('PROLIFIC_PID', None)
        
        annotator, created = Annotator.objects.get_or_create(prolific_pid=pid)
        
        # Always update metadata to capture the latest session info if provided
        if metadata:
            annotator.metadata.update(metadata)
            annotator.save()

        # Get or create enrollment to check project-specific progress
        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project, 
            annotator=annotator,
            defaults={'target_tasks': project.target_tasks_per_annotator}
        )

        # Calculate current state
        current_step = 'CONSENT'
        if annotator.consent_accepted:
            current_step = 'INSTRUCTIONS'
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
        return Response({"status": "ok", "next_step": "INSTRUCTIONS"})

class CompleteOnboarding(APIView):
    """ Saves that the user completed instructions/training """
    def post(self, request):
        pid = request.data.get('pid')
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        annotator.onboarding_completed = True
        annotator.save()
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
        
        # Copy data and manually add the annotator
        data = request.data.copy()
        
        # The frontend sends only 'document', 'result', etc.
        # We retrieve the annotator from the PID for security.
        serializer = AnnotationSerializer(data=data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # SAVE THE ANNOTATION
                    annotation = serializer.save(annotator=annotator)
                    
                    # --- SCREENING / TRAINING LOGIC ---
                    # Retrieve enrollment to check the status
                    document = annotation.document
                    project = document.project
                    
                    enrollment, _ = ProjectEnrollment.objects.get_or_create(
                        project=project,
                        annotator=annotator
                    )
                    
                    # --- QUALITY CONTROL / SCREENING LOGIC ---
                    if document.is_gold_unit:
                        # Increment gold task counter
                        enrollment.training_tasks_completed += 1
                        
                        # Evaluate correctness (Simple exact match logic)
                        is_correct = False
                        if document.gold_solution:
                            user_class = data.get('result', {}).get('classification')
                            gold_class = document.gold_solution.get('classification')
                            if user_class == gold_class:
                               is_correct = True
                        
                        # Update cumulative accuracy
                        prev_acc = enrollment.training_accuracy or 0.0
                        total = enrollment.training_tasks_completed
                        prev_correct = prev_acc * (total - 1)
                        current_correct = prev_correct + (1 if is_correct else 0)
                        new_acc = current_correct / total
                        
                        enrollment.training_accuracy = new_acc
                        enrollment.save()

                return Response({"status": "saved"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Handles the case where the user tries to save the same document twice (UniqueConstraint)
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetNextTask(APIView):
    """
    DETERMINES THE NEXT TASK FOR THE ANNOTATOR
    ---------------------------------------------------------
    Logic:
    1. Check for exclusion or already meeting target tasks.
    2. Check screening status (Training phase or Passed phase).
    3. If training -> Force a Gold Unit.
    4. If passed -> Gold Injection logic OR Normal document selection based on project strategy.
    5. Concurrent safe selection using SKIP LOCKED.
    """
    def get(self, request):
        # 1. RETRIEVE PARAMETERS
        pid = request.query_params.get('pid')
        project_id = request.query_params.get('project_id')

        if not pid or not project_id:
            return Response({"error": "Missing 'pid' or 'project_id'"}, status=400)

        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        project = get_object_or_404(Project, id=project_id)

        # 2. BASIC STATUS CHECKS
        if not project.is_active:
            return Response({"status": "stopped", "message": "This project is currently not accepting annotations."})

        # 3. SCREENING / ENROLLMENT LOGIC
        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project, 
            annotator=annotator,
            defaults={'target_tasks': project.target_tasks_per_annotator}
        )

        if enrollment.exclude_from_distribution:
            return Response({"status": "stopped", "message": "Access denied for this project."})

        # Check user progress for THIS project
        done_count = annotator.annotations.filter(document__project=project).count()
        if done_count >= enrollment.target_tasks:
            return self._completed_response()
        
        if enrollment.screening_status == 'FAILED':
             return Response({"status": "stopped", "message": "Screening not passed."})
            
        if enrollment.screening_status == 'PENDING':
            # Check if they have met the training requirements but status hasn't updated
            screening_config = project.screening_config or {}
            req_training = screening_config.get('training_tasks_required', 0)
            
            if enrollment.training_tasks_completed >= req_training:
                enrollment.screening_status = 'PASSED'
                enrollment.save()

        # 4. TASK SELECTION (Concurrency Safe)
        with transaction.atomic():
            target_id = self._get_candidate_id(project, annotator, enrollment, done_count)
            
            if not target_id:
                # If we are in training and no gold units are left, or no docs left
                if enrollment.screening_status == 'PENDING':
                    return Response({"status": "no_training_data"})
                return self._completed_response()

            # select_for_update allows us to lock the row and avoid double assignment in Race Conditions
            final_doc = Document.objects.select_for_update(skip_locked=True).filter(id=target_id).first()

        # 5. RESPONSE ASSEMBLY
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
        screening_config = project.screening_config or {}
        injection_freq = screening_config.get('gold_injection_frequency', 0)
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
            # Respect max capacity and prioritize based on setup
            candidates = candidates.filter(num_anns__lt=project.max_annotations_per_doc)
            order = 'num_anns' if project.prioritize_unannotated else '?'
            candidates = candidates.order_by(order)
            
        elif project.distribution_strategy == 'FULL_OVERLAP':
            # Everyone sees everything, just random
            candidates = candidates.order_by('?')
        
        return candidates.values_list('id', flat=True).first()

    def _task_response(self, doc, enrollment):
        """ Prepares the final Response JSON, filtering out sensitive data """
        # The Serializer already excludes 'metadata' and 'external_id' for privacy
        serializer = DocumentSerializer(doc)
        data = serializer.data 
        
        # Add frontend-specific tags
        data.update({
            'is_gold': doc.is_gold_unit,
            # We can keep feedback_enabled if we want to show feedback 
            # but the user explicitly asked to hide the banner in pending.
            'feedback_enabled': enrollment.screening_status == 'PENDING'
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
        if not pid or not project_id:
            return Response({"error": "Missing PID or Project ID"}, status=400)
        
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        project = get_object_or_404(Project, id=project_id)
        
        if not project.is_active:
            return Response({"error": "Project is not active"}, status=404)
        
        if annotator.consent_accepted:
            return Response({"error": "Already consented"}, status=400)

        return Response({
            "consent_text": project.informed_consent_config
        })