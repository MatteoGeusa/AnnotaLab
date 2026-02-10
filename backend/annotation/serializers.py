from rest_framework import serializers
from .models import Project, Document, Annotation, Annotator
import json
import os
from django.conf import settings

# Load default config at startup (more efficient)
CONFIG_PATH = os.path.join(settings.BASE_DIR, 'config', 'default_project_config.json')
try:
    with open(CONFIG_PATH, 'r') as f:
        DEFAULT_CONFIG = json.load(f)
except Exception as e:
    print(f"Error loading default config: {e}")
    DEFAULT_CONFIG = {}

class DocumentSerializer(serializers.ModelSerializer):
    """
    The document serializer sends the text and the project configuration to the frontend
    """
    project_config = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'text', 'external_id', 'project_config', 'metadata']

    def get_project_config(self, obj):
        # Merge DB config with default config / Merge config DB con default
        db_config = obj.project.configuration
        
        # Handle string case (bug fix for some DBs) / Gestione caso stringa
        if isinstance(db_config, str):
            try:
                db_config = json.loads(db_config)
            except json.JSONDecodeError:
                db_config = {}

        # Safe merge: start with default, overlay DB config
        final_config = DEFAULT_CONFIG.copy()
        
        if isinstance(db_config, dict):
            final_config.update(db_config)
            
        return final_config

class AnnotationSerializer(serializers.ModelSerializer):
    """ 
    The annotation serializer receives the annotation result from the frontend
    """
    class Meta:
        model = Annotation
        fields = ['document', 'result', 'milliseconds_to_complete']