from django.db import models
from django.core.exceptions import ValidationError

from django.db.models import JSONField 
from django.utils import timezone
import uuid

class Project(models.Model):
    """
    Represents an annotation 'campaign' or 'batch'.
    Example: 'Sentiment Analysis Batch 1'
    """
    name = models.CharField(max_length=200, help_text="Project name")
    description = models.TextField(blank=True, help_text="Project description")

    # CONFIGURATION FOR PSYCOMARK:
    # The JSON should contain definitions for both span highlighting and classification.
    # Example structure:
    # {
    #   "task_type": "hybrid",
    #   "span_labels": [
    #       {"name": "Actor", "color": "#FF5733"}, 
    #       {"name": "Action", "color": "#33FF57"},
    #       {"name": "Victim", "color": "#3357FF"},
    #       {"name": "Effect", "color": "#F333FF"},
    #       {"name": "Evidence", "color": "#FF33F6"}
    #   ],
    #   "class_labels": [
    #       {"value": "Yes", "label": "Conspiracy"},
    #       {"value": "No", "label": "Not Conspiracy"},
    #       {"value": "Can't tell", "label": "Ambiguous"}
    #   ]
    # }
    configuration = JSONField(default=dict, help_text="Frontend configuration (labels, colors, UI settings)")

    # Textual instructions for the annotator (supports Markdown/HTML)
    guidelines = models.TextField(blank=True, help_text="Textual instructions for the annotator (supports Markdown/HTML)")

    dataset_file = models.FileField(
        upload_to='datasets/', 
        blank=True, 
        null=True, 
        help_text="Carica un file .jsonl per popolare automaticamente i documenti."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    def __str__(self):
        return self.name


class Annotator(models.Model):
    prolific_pid = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = JSONField(default=dict, blank=True)
    
    # --- NUOVI CAMPI PER IL FLUSSO ---
    consent_accepted = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False) # Istruzioni + Training
    
    # Quanti task deve fare in totale? (Default 10)
    target_tasks = models.IntegerField(default=10)

    objects = models.Manager()

    def __str__(self):
        return f"{self.prolific_pid} (Consenso: {self.consent_accepted})"


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
    # How many annotations do we want for this document? (e.g. 3)
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
    seconds_to_complete = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        # An annotator cannot annotate the same document twice, the DB will raise an error if they try.
        unique_together = ('document', 'annotator')

    def __str__(self):
        return f"Annotation {self.id} by {self.annotator}"