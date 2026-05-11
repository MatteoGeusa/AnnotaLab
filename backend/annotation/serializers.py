from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
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
        config = obj.project.annotation_schema or {}

        # Handle string case (bug fix for some DBs)
        if isinstance(config, str):
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                config = {}

        if not isinstance(config, dict):
            config = {}

        return config

class AnnotationSerializer(serializers.ModelSerializer):
    """
    Receives the annotation result from the frontend.
    Validates that the submitted document belongs to the correct project
    to prevent cross-project annotation injection.
    """
    class Meta:
        model = Annotation
        fields = ['document', 'result', 'milliseconds_to_complete']

    def validate_document(self, document):
        """Ensure the document belongs to the project the annotator is working on."""
        request = self.context.get('request')
        if request is not None:
            data = request.data
            project_slug = data.get('project_slug')
            project_id = data.get('project_id')
            try:
                if project_slug:
                    project = Project.objects.get(slug=project_slug)
                elif project_id:
                    project = Project.objects.get(id=project_id)
                else:
                    return document  # No project context available; skip check
                if document.project_id != project.pk:
                    raise serializers.ValidationError(
                        "Document does not belong to the specified project."
                    )
            except ObjectDoesNotExist:
                pass  # Project lookup failed; let the view handle it
        return document
