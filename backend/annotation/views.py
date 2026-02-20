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
        
        annotator, created = Annotator.objects.get_or_create(prolific_pid=pid)
        project = get_object_or_404(Project, id=project_id) if project_id else None
        
        # Calculate current state
        current_step = 'CONSENT'
        if annotator.consent_accepted:
            current_step = 'INSTRUCTIONS'
        if annotator.onboarding_completed:
            current_step = 'ANNOTATION'
            
        # Check if already completed
        done_count = annotator.annotations.count()
        if done_count >= annotator.target_tasks:
            current_step = 'COMPLETED'

        return Response({
            "status": "ok",
            "pid": annotator.prolific_pid,
            "step": current_step,
            "done_count": done_count,
            "project_name": project.name if project else None,
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
                    
                    # Check if we are in screening/pending status AND this was a gold unit
                    if enrollment.screening_status == 'PENDING' and document.is_gold_unit:
                        # Increment counter
                        enrollment.training_tasks_completed += 1
                        
                        # Evaluate correctness (Simple exact match or logic)
                        # For now: we assume gold_solution structure matches result structure
                        # Ideally, you'd have a helper function: check_correctness(result, gold)
                        is_correct = False
                        if document.gold_solution:
                            # SIMPLE COMPARISON (Can be improved)
                            # We compare the 'classification' value
                            user_class = data.get('result', {}).get('classification')
                            gold_class = document.gold_solution.get('classification')
                            if user_class == gold_class:
                               is_correct = True
                            
                            # TODO: Add span logic comparison if needed
                            
                        # Update accuracy (Rolling average or just count correct)
                        # Let's verify against requirements
                        req_accuracy = project.screening_config.get('min_accuracy_required', 0.0)
                        req_tasks = project.screening_config.get('training_tasks_required', 0)
                        
                        # If this is the N-th task or later, check if they pass/fail
                        # But wait, 'training_accuracy' field needs to be updated. 
                        # Simpler approach: we don't store "training_accuracy" percentage in DB yet, 
                        # we just need to know if they passed the threshold.
                        # Let's assume we store the number of correct answers in metadata for now or add a field if needed.
                        # Since we didn't add 'correct_answers_count' to model, let's use survey_data or metadata hack 
                        # OR just re-calculate from DB?
                        # "enrollment.training_accuracy" is a Float. Let's use it as current accuracy.
                        
                        prev_acc = enrollment.training_accuracy or 0.0
                        total = enrollment.training_tasks_completed
                        # Recover previous correct count: prev_acc * (total - 1)
                        prev_correct = prev_acc * (total - 1)
                        current_correct = prev_correct + (1 if is_correct else 0)
                        new_acc = current_correct / total
                        
                        enrollment.training_accuracy = new_acc
                        
                        # Check if training is finished
                        if total >= req_tasks:
                            if new_acc >= req_accuracy:
                                enrollment.screening_status = 'PASSED'
                            else:
                                # Allow them to continue? Or Fail immediately?
                                # Usually Fail immediately if they cross the threshold of "no return"
                                # But here we just check at the "req_tasks" mark.
                                enrollment.screening_status = 'FAILED'
                                
                        enrollment.save()

                return Response({"status": "saved"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Handles the case where the user tries to save the same document twice (UniqueConstraint)
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubmitSurvey(APIView):
    def post(self, request):
        pid = request.data.get('pid')
        project_id = request.data.get('project_id')
        survey_data = request.data.get('survey_data')
        
        if not pid or not project_id or not survey_data:
            return Response({"error": "Missing data"}, status=400)
            
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        project = get_object_or_404(Project, id=project_id)
        
        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project, 
            annotator=annotator
        )
        
        enrollment.survey_data = survey_data
        enrollment.save()
        
        return Response({"status": "ok"})

class GetNextTask(APIView):
    def get(self, request):
        # RECUPERO PARAMETRI
        pid = request.query_params.get('pid')
        project_id = request.query_params.get('project_id')

        if not pid or not project_id:
            return Response({"error": "Missing 'pid' or 'project_id'"}, status=400)

        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        project = get_object_or_404(Project, id=project_id)

        # CONTROLLO ESCLUSIONE
        if annotator.exclude_from_distribution:
            return Response({
                "status": "stopped"
            })

        # CONTROLLO LIMITE TASK UTENTE
        done_count = annotator.annotations.filter(document__project=project).count()
        if done_count >= annotator.target_tasks:
            return Response({
                "status": "completed", 
                "completion_url": PROLIFIC_COMPLETION_URL
            })

        final_doc = None

        # LOGICA DI ASSEGNAZIONE
        
        # 0. CONTROLLO SCREENING (SURVEY + TRAINING)
        enrollment, _ = ProjectEnrollment.objects.get_or_create(
            project=project, 
            annotator=annotator
        )
        
        if enrollment.screening_status == 'FAILED':
             return Response({
                "status": "stopped",
                "message": "Screening not passed."
            })
            
        if enrollment.screening_status == 'PENDING':
            # Check 1: Survey logic removed (Directly to Training)
            screening_config = project.screening_config or {}

            
            # Check 2: Training Tasks
            req_training = screening_config.get('training_tasks_required', 0)
            if enrollment.training_tasks_completed < req_training:
                # They need a training task.
                # Serve a Gold Unit.
                # Use same logic as A1 but specifically looking for one they haven't done?
                # Actually A1 logic below does exactly that (excludes annotations__annotator=ann).
                # But we need to ensure we DO find one, or fail.
                # And we want to mark it as FEEDBACK ENABLED.
                
                # Let's re-use the atomic block logic but force IS_GOLD_UNIT search.
                pass # Proceed to transaction block, but we will force "gold_only" logic
                
            else:
                # If they completed the count but status is still PENDING, 
                # check if they passed (logic in submit should have handled this, 
                # but valid check here too).
                # If logic in submit didn't fail them, and they are > req, pass them?
                # For safety, if they are here and have tasks >= req, we assume they passed 
                # or we just switch them to PASSED now if not set.
                enrollment.screening_status = 'PASSED'
                enrollment.save()

        with transaction.atomic():
            
            target_id = None
            
            # --- SCREENING OVERRIDE ---
            if enrollment.screening_status == 'PENDING':
                # Force search for Gold Unit
                 gold_candidate_id = Document.objects.filter(
                    project=project,
                    is_gold_unit=True
                ).exclude(
                    annotations__annotator=annotator
                ).values_list('id', flat=True).first()
                
                 target_id = gold_candidate_id
                 
                 # If no gold unit available for training?
                 if not target_id:
                     return Response({"status": "no_training_data"})
            
            else:
                # FASE A: Cerca ID Candidato (Senza Locking)
                # Qui usiamo annotate/filter liberamente perché non blocchiamo nulla
                
                target_id = None
                
                # A1. ONGOING QUALITY CONTROL (Gold Injection)
                # Check if we should inject a gold unit based on frequency
                # Changed: frequency is now in task_type_config (Business Logic of the Task)
                task_config = project.task_type_config or {}
                injection_freq = task_config.get('gold_injection_frequency', 0)
                
                should_inject_gold = False
                if injection_freq > 0:
                    # Logic: If I have done N tasks, and (N+1) % freq == 0, then serve Gold.
                    # Example: Freq=5. Done=4. (4+1)%5 == 0 -> True. Serve Gold.
                    # Example: Done=9. (9+1)%5 == 0 -> True. Serve Gold.
                    if (done_count + 1) % injection_freq == 0:
                        should_inject_gold = True
                
                if should_inject_gold:
                    gold_candidate_id = Document.objects.filter(
                        project=project,
                        is_gold_unit=True
                    ).exclude(
                        annotations__annotator=annotator
                    ).values_list('id', flat=True).first()
                    
                    if gold_candidate_id:
                        target_id = gold_candidate_id
                
                # If no gold check or no gold found, target_id is still None.


                # A2. DOCUMENTI NORMALI (Se non c'è Gold Unit)
                if not target_id:
                    # Query base
                    base_qs = Document.objects.filter(
                        project=project,
                        is_gold_unit=False
                    ).exclude(
                        annotations__annotator=annotator
                    ).annotate(
                        num_anns=Count('annotations')
                    )

                    # Applicazione Strategia per trovare l'ID
                    candidates = base_qs
                    
                    if project.distribution_strategy == 'STANDARD':
                        candidates = candidates.filter(num_anns__lt=project.max_annotations_per_doc)
                        if project.prioritize_unannotated:
                            candidates = candidates.order_by('num_anns')
                        else:
                            candidates = candidates.order_by('?')
                    
                    elif project.distribution_strategy == 'FULL_OVERLAP':
                        candidates = candidates.order_by('?')
                    
                    elif project.distribution_strategy == 'METADATA_MATCH':
                        user_group = annotator.metadata.get('group')
                        if user_group:
                            candidates = candidates.filter(
                                metadata__group=user_group,
                                num_anns__lt=project.max_annotations_per_doc
                            )
                    
                    # Prendiamo solo l'ID del primo risultato
                    target_id = candidates.values_list('id', flat=True).first()

            # Ora che abbiamo l'ID, possiamo bloccare la riga specifica senza usare annotate/group_by
            if target_id:
                # select_for_update funziona perfettamente su una .get() o .filter() semplice
                final_doc = Document.objects.select_for_update(skip_locked=True).filter(id=target_id).first()

        # 4. RISPOSTA
        if final_doc:
            from .serializers import DocumentSerializer
            serializer = DocumentSerializer(final_doc)
            data = serializer.data 
            
            # Add type metadata
            if enrollment.screening_status == 'PENDING':
                data['type'] = 'TRAINING'
                data['feedback_enabled'] = True
            else:
                data['type'] = 'NORMAL'
                
            return Response(data)
        else:
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
        
        if annotator.consent_accepted:
            return Response({"error": "Already consented"}, status=400)

        return Response({
            "consent_text": project.informed_consent_config
        })