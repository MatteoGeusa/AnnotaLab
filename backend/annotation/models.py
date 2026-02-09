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

    # Since we use Postgres, this field will be used to save frontend configuration and results
    # JSON Example: {"labels": [{"name": "PER", "color": "red"}, {"name": "LOC", "color": "blue"}]}
    # The Vue frontend will read this field to know which buttons to show.
    configuration = JSONField(default=dict, help_text="JSON configuration for the frontend (labels, colors, instructions)")
    
    # Textual instructions for the annotator (supports Markdown/HTML)
    guidelines = models.TextField(blank=True, help_text="Textual instructions for the annotator (supports Markdown/HTML)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    def __str__(self):
        return self.name


class Annotator(models.Model):
    """
    The user performing the work. We only need the unique platform ID.
    """
    prolific_pid = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional metadata if Prolific passes demographic info
    metadata = JSONField(default=dict, blank=True)

    objects = models.Manager()

    def __str__(self):
        return self.prolific_pid


class Document(models.Model):
    """
    The text unit to be annotated.
    """
    # Unique document ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Link the document to a batch
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    
    # The actual text
    text = models.TextField()
    
    # External ID (e.g. ID from the original dataset)
    external_id = models.CharField(max_length=100, blank=True, null=True)
    
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
    
    # The actual highlight data.
    # Example: [{"start": 0, "end": 5, "label": "PER", "text": "Mario"}]
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