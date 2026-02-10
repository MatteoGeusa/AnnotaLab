from django.db import models
from django.core.exceptions import ValidationError

from django.db.models import JSONField 
from django.utils import timezone
import uuid
import os
from django.conf import settings
import json

def get_default_configuration():
    config_path = os.path.join(settings.BASE_DIR, 'config', 'default_project_config.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"task_type": "classification", "class_labels": []}
            
    return {
        "task_type": "hybrid",
        "span_labels": [{"name": "Evidence", "color": "#FFA500"}],
        "class_labels": [{"value": "Yes", "label": "Yes"}, {"value": "No", "label": "No"}]
    }

class Project(models.Model):
    """
    Represents an annotation 'campaign' or 'batch'.
    Example: 'Sentiment Analysis Batch 1'
    """
    name = models.CharField(max_length=200, help_text="Project name")
    description = models.TextField(blank=True, help_text="Project description")

    # CONFIGURATION
    configuration = models.JSONField(
        default=get_default_configuration, 
        help_text="Frontend configuration (labels, colors, UI settings)"
    )

    # Questo serve per l'upload manuale dall'admin (quello che abbiamo fatto prima)
    configuration_file = models.FileField(
        upload_to='configs/', 
        blank=True, 
        null=True,
        help_text="Opzionale: Carica un file JSON per sovrascrivere la configurazione."
    )

    STRATEGY_CHOICES = [
        ('STANDARD', 'Standard (Pool Pubblico)'),
        ('FULL_OVERLAP', 'Tutti vedono tutto (Alta Ridondanza)'),
        ('METADATA_MATCH', 'Assegnazione per Gruppi (Metadata Based)'),
    ]
    
    distribution_strategy = models.CharField(
        max_length=20, 
        choices=STRATEGY_CHOICES, 
        default='STANDARD',
        help_text="Definisce come i documenti vengono assegnati agli annotatori."
    )

    # --- VINCOLI DI RIDONDANZA ---
    min_annotations_per_doc = models.IntegerField(
        default=3, 
        help_text="Obiettivo: Quante persone devono annotare ogni documento."
    )
    
    max_annotations_per_doc = models.IntegerField(
        default=5, 
        help_text="Hard Cap: Smetti di servire il documento se raggiunge questo numero (evita sprechi)."
    )

    # Serve per dire: "Se un documento ha 2 annotazioni e gli altri 0, dai priorità a quelli con 0?"
    prioritize_unannotated = models.BooleanField(
        default=True,
        help_text="Se True, il sistema cercherà di finire prima i documenti mai visti."
    )

    dataset_file = models.FileField(
        upload_to='datasets/', 
        blank=True, 
        null=True, 
        help_text="Upload a .jsonl file to automatically populate documents."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    def __str__(self):
        return self.name


class Annotator(models.Model):
    prolific_pid = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = JSONField(default=dict, blank=True)
    consent_accepted = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False) # Instructions + Training
    
    # BUSINESS LOGIC: WORKLOAD
    # ---------------------------------------------------------
    # Defines how many tasks an annotator must complete before finishing the session.
    # Default is 10. Increase this for longer sessions, decrease for shorter pilots.
    target_tasks = models.IntegerField(default=10)

    objects = models.Manager()

    def __str__(self):
        return f"{self.prolific_pid} (Consent: {self.consent_accepted})"


class Document(models.Model):
    """
    The text unit to be annotated.
    """
    # Unique document ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link the document to a batch
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    
    # The actual text content.
    # Since the source dataset is redacted, this field might need to be populated 
    # via Reddit API using the external_id.
    text = models.TextField()
    
    # External ID (e.g. ID from the original dataset)
    external_id = models.CharField(max_length=100, blank=True, null=True)

    # Metadata for context (e.g., {"subreddit": "conspiracy", "thread_id": "..."})
    metadata = JSONField(default=dict, blank=True)
    
    # GOLD UNITS MANAGEMENT (Quality Control)
    # If True, this document has a known correct answer.
    is_gold_unit = models.BooleanField(default=False)
    # The correct answer (in JSON format) for automatic comparison
    gold_solution = JSONField(default=dict, blank=True, null=True)

    # REDUNDANCY MANAGEMENT (CRITICAL)
    # BUSINESS LOGIC: REDUNDANCY
    # ---------------------------------------------------------
    # Controls the number of distinct annotators required for each document.
    # - 1 = Single annotation (High risk of noise).
    # - 3 = Standard for majority voting.
    # - 5+ = High precision required.
    min_annotations_required = models.IntegerField(default=3)
    
    # Denormalized counter. 
    # Every time an annotation arrives, we increment this number.
    # Used for very fast queries like: "Get all docs with count < 3"
    current_annotations_count = models.IntegerField(default=0, db_index=True)

    objects = models.Manager()

    def __str__(self):
        return f"Doc {self.id} ({self.current_annotations_count}/{self.min_annotations_required})"


class Annotation(models.Model):
    """
    Links an Annotator to a Document.
    """
    # Unique annotation ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link the annotation to a document
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='annotations')
    # Link the annotation to an annotator
    annotator = models.ForeignKey(Annotator, on_delete=models.PROTECT, related_name='annotations')
    
    # THE RESULT PAYLOAD
    # Expected structure for PsyCoMark:
    # {
    #   "classification": "Yes",
    #   "spans": [
    #       {"start": 10, "end": 20, "label": "Actor", "text": "The government"}
    #   ]
    # }
    result = JSONField()
    
    # How long it took (useful to discard those taking 2 seconds = bot/spam)
    milliseconds_to_complete = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        # An annotator cannot annotate the same document twice, the DB will raise an error if they try.
        unique_together = ('document', 'annotator')

    def __str__(self):
        return f"Annotation {self.id} by {self.annotator}"