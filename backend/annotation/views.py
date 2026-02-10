from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.conf import settings
from .models import Document, Annotator, Annotation, Project
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
        if not pid:
            return Response({"error": "Missing PID"}, status=400)
        
        annotator, created = Annotator.objects.get_or_create(prolific_pid=pid)
        
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
                serializer.save(annotator=annotator)
                return Response({"status": "saved"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Handles the case where the user tries to save the same document twice (UniqueConstraint)
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        with transaction.atomic():
            
            # FASE A: Cerca ID Candidato (Senza Locking)
            # Qui usiamo annotate/filter liberamente perché non blocchiamo nulla
            
            # A1. GOLD UNITS
            gold_candidate_id = Document.objects.filter(
                project=project,
                is_gold_unit=True
            ).exclude(
                annotations__annotator=annotator
            ).values_list('id', flat=True).first()

            target_id = gold_candidate_id

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
            data['project_config'] = project.configuration 
            return Response(data)
        else:
            return Response({
                "status": "completed", 
                "completion_url": PROLIFIC_COMPLETION_URL
            })