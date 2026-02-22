from rest_framework import serializers
from .models import Project, Document, Annotation, Annotator
import json


class DocumentSerializer(serializers.ModelSerializer):
    """
    The document serializer sends the text and the project configuration to the frontend.
    The default config is already set in models.py at project creation time (single source of truth).
    """
    project_config = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'text', 'project_config']

    def get_project_config(self, obj):
        config = obj.project.task_type_config or {}

        # Handle string case (bug fix for some DBs)
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = {}

        if not isinstance(config, dict):
            config = {}

        # Remove internal/sensitive fields before sending to frontend
        config.pop('gold_injection_frequency', None)
        config.pop('task_type', None)

        return config

class AnnotationSerializer(serializers.ModelSerializer):
    """ 
    The annotation serializer receives the annotation result from the frontend
    """
    class Meta:
        model = Annotation
        fields = ['document', 'result', 'milliseconds_to_complete']