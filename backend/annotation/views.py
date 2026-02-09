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
    Restituisce lo STATO dell'utente per dire al Frontend che pagina mostrare.
    """
    def post(self, request):
        pid = request.data.get('prolific_pid')
        if not pid:
            return Response({"error": "Missing PID"}, status=400)
        
        annotator, created = Annotator.objects.get_or_create(prolific_pid=pid)
        
        # Calcoliamo lo stato attuale
        current_step = 'CONSENT'
        if annotator.consent_accepted:
            current_step = 'INSTRUCTIONS'
        if annotator.onboarding_completed:
            current_step = 'ANNOTATION'
            
        # Controlliamo se ha già finito
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
    """ Salva che l'utente ha accettato il consenso """
    def post(self, request):
        pid = request.data.get('pid')
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        annotator.consent_accepted = True
        annotator.save()
        return Response({"status": "ok", "next_step": "INSTRUCTIONS"})

class CompleteOnboarding(APIView):
    """ Salva che l'utente ha finito istruzioni/training """
    def post(self, request):
        pid = request.data.get('pid')
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        annotator.onboarding_completed = True
        annotator.save()
        return Response({"status": "ok", "next_step": "ANNOTATION"})

class SubmitAnnotation(APIView):
    """
    Endpoint: POST /api/v1/submit/
    Salva il lavoro dell'utente.
    """
    def post(self, request):
        pid = request.data.get('pid')
        if not pid:
            return Response({"error": "Missing PID"}, status=status.HTTP_400_BAD_REQUEST)
            
        annotator = get_object_or_404(Annotator, prolific_pid=pid)
        
        # Copiamo i dati e aggiungiamo l'annotatore manualmente
        data = request.data.copy()
        
        # Il frontend ci manda solo 'document', 'result', ecc.
        # L'annotatore lo prendiamo dal PID per sicurezza.
        serializer = AnnotationSerializer(data=data)
        
        if serializer.is_valid():
            try:
                serializer.save(annotator=annotator)
                return Response({"status": "saved"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Gestisce il caso in cui prova a salvare due volte lo stesso documento (UniqueConstraint)
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetNextTask(APIView):
    def get(self, request):
        pid = request.query_params.get('pid')
        annotator = get_object_or_404(Annotator, prolific_pid=pid)

        # 1. CONTROLLO LIMITE TASK (es. 10)
        done_count = annotator.annotations.count()
        if done_count >= annotator.target_tasks:
            return Response({
                "status": "completed", 
                "completion_url": PROLIFIC_COMPLETION_URL
            })

        # 2. LOGICA GOLD UNITS (Test in itinere)
        # Ogni tanto (es. il 3° e il 7° task) diamo una Gold Unit.
        # Qui facciamo una logica semplice: se esiste una Gold Unit non fatta, dallo.
        # Altrimenti dai un documento normale.
        
        with transaction.atomic():
            # A. Cerca prima una Gold Unit non ancora fatta dall'utente
            next_doc = Document.objects.filter(
                is_gold_unit=True
            ).exclude(
                annotations__annotator=annotator
            ).first()

            # B. Se non ci sono Gold Unit disponibili, prendi un doc normale
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
                # Finiti i documenti nel DB
                return Response({
                    "status": "completed", 
                    "completion_url": PROLIFIC_COMPLETION_URL
                })