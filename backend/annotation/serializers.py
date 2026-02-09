from rest_framework import serializers
from .models import Project, Document, Annotation, Annotator

class DocumentSerializer(serializers.ModelSerializer):
    """
    Invia al frontend il testo e la configurazione del progetto (etichette, colori).
    """
    project_config = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'text', 'external_id', 'project_config', 'metadata']

    def get_project_config(self, obj):
        # Passiamo la configurazione (colori, label) direttamente nel documento
        return obj.project.configuration

class AnnotationSerializer(serializers.ModelSerializer):
    """
    Riceve dal frontend il risultato dell'annotazione.
    """
    class Meta:
        model = Annotation
        fields = ['document', 'result', 'seconds_to_complete']