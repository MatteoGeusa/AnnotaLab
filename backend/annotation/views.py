from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.conf import settings
from .models import Document, Annotator, Annotation, Project
from .serializers import DocumentSerializer, AnnotationSerializer

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
        pid = request.query_params.get('pid')
        annotator = get_object_or_404(Annotator, prolific_pid=pid)

        # 1. TASK LIMIT CHECK (e.g. 10)
        done_count = annotator.annotations.count()
        if done_count >= annotator.target_tasks:
            return Response({
                "status": "completed", 
                "completion_url": PROLIFIC_COMPLETION_URL
            })

        # TASK ASSIGNMENT / ASSEGNAZIONE TASK
        # EN: This is the core logic for distributing work to crowd workers.
        #     Priority 1: Gold Units (Quality Checks).
        #         - If there are Gold Units the user hasn't seen yet, assign one.
        #         - This ensures we can measure annotator quality.
        #     Priority 2: Normal Documents (Redundancy Management).
        #         - Assign documents that have NOT reached the redundancy target (e.g. < 3 annotations).
        #         - 'select_for_update' locks the row to prevent race conditions during high concurrency.
        #         - 'skip_locked=True' prevents workers from waiting; they just skip to the next available doc.
        #
        # IT: Questa è la logica centrale per distribuire il lavoro ai worker.
        #     Priorità 1: Gold Units (Controllo Qualità).
        #         - Se ci sono Gold Unit che l'utente non ha ancora visto, assegnane una.
        #         - Questo assicura di poter misurare la qualità dell'annotatore.
        #     Priorità 2: Documenti Normali (Gestione Ridondanza).
        #         - Assegna documenti che NON hanno raggiunto il target di ridondanza (es. < 3 annotazioni).
        #         - 'select_for_update' blocca la riga per prevenire race condition con alta concorrenza.
        #         - 'skip_locked=True' evita che i worker aspettino; passano semplicemente al prossimo doc libero.
        
        with transaction.atomic():
            # A. First search for a Gold Unit not yet completed by the user
            next_doc = Document.objects.filter(
                is_gold_unit=True
            ).exclude(
                annotations__annotator=annotator
            ).first()

            # B. If no Gold Units are available, take a normal doc
            if not next_doc:
                next_doc = Document.objects.select_for_update(skip_locked=True).filter(
                    is_gold_unit=False,
                    current_annotations_count__lt=3 
                ).exclude(
                    annotations__annotator=annotator
                ).order_by('-current_annotations_count').first()

            if next_doc:
                serializer = DocumentSerializer(next_doc)
                return Response(serializer.data)
            else:
                # No more documents to annotate
                # Nessun documento disponibile
                return Response({
                    "status": "completed", 
                    "completion_url": PROLIFIC_COMPLETION_URL
                })