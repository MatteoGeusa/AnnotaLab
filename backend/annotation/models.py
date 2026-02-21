from django.db import models
from django.core.exceptions import ValidationError

from django.db.models import JSONField 
from django.utils import timezone
import uuid
import os
from django.conf import settings
import json

def get_default_configuration_for_task_type():
    config_path = os.path.join(settings.BASE_DIR, 'config_defaults', 'default_project_config.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"task_type": "classification", "class_labels": []}
            
    return {
        "task_type": "hybrid",
        "span_labels": [{"name": "Evidence", "color": "#FFA500"}],
        "class_labels": [{"value": "Yes", "label": "Yes"}, {"value": "No", "label": "No"}],
        "gold_injection_frequency": 5
    }

def get_default_configuration_for_screening():
    return {
        "training_tasks_required": 0,
        "min_accuracy_required": 0.0
    }

def get_default_configuration_for_informed_consent():
    return """
    [EXAMPLE SCRIPT]
    Welcome to the study!
    
    Your task: You will be asked to [describe the task in half a line, e.g., read and classify 20 sentences]. The estimated time is approximately [X] minutes. The goal is [very brief purpose, e.g., to improve an artificial intelligence system].
    
    Your data and privacy: This task is anonymous. We do not collect any personally identifiable information. We will only save your responses and your Prolific ID, which we need exclusively to confirm your completion of the task and authorize your payment on the platform.
    
    Your rights: Participation is voluntary. You may stop participating at any time. If you decide not to finish, simply close this page and click on "Return submission" on Prolific. In this case, your partial data will not be used, but we will not be able to process your payment.
    
    By clicking the button below, you confirm that you are at least 18 years old, that you have read this information, and that you consent to participate.
    """

class Project(models.Model):
    """
    Represents an annotation 'campaign' or 'batch'.
    Example: 'Sentiment Analysis Batch 1'
    """
    name = models.CharField(max_length=200, help_text="Project name")
    description = models.TextField(blank=True, help_text="Project description")
    is_active = models.BooleanField(default=True, help_text="If False, the project will not accept new annotations.")

    dataset_text_key = models.CharField(
        max_length=100, 
        default='text',
        help_text="The JSON key containing the text to be annotated (e.g., 'text', 'body', 'content')."
    )
    
    dataset_id_key = models.CharField(
        max_length=100, 
        default='_id',
        blank=True,
        help_text="The JSON key for the ID. If empty or not found, it will use the row number."
    )

    # CONFIGURATION

    informed_consent_config = models.TextField(
        default=get_default_configuration_for_informed_consent, 
        help_text="Informed Consent Configuration: accept a string can be showed to the annotator before starting the task"
    )
    
    task_type_config = models.JSONField(
        default=get_default_configuration_for_task_type, 
        help_text="Task Configuration (labels, colors, questions)"
    )

    screening_config = models.JSONField(
        default=get_default_configuration_for_screening,
        blank=True,
        help_text="Configuration for screening: { 'training_tasks_required': int, 'min_accuracy_required': float }"
    )

    configuration_task_type_file = models.FileField(
        upload_to='config_uploads/', 
        blank=True, 
        null=True,
        help_text="Optional: Upload a JSON file to overwrite the Task configuration (Labels, Questions)."
    )
    
    configuration_screening_file = models.FileField(
        upload_to='config_uploads/', 
        blank=True, 
        null=True,
        help_text="Optional: Upload a JSON file to overwrite the Screening configuration (Survey, Training)."
    )

    STRATEGY_CHOICES = [
        ('STANDARD', 'Standard (Public Pool)'),
        ('FULL_OVERLAP', 'Everyone sees everything (High Redundancy)'),
        ('METADATA_MATCH', 'Group Assignment (Metadata Based)'),
    ]
    
    distribution_strategy = models.CharField(
        max_length=20, 
        choices=STRATEGY_CHOICES, 
        default='STANDARD',
        help_text="Defines how documents are assigned to annotators."
    )

    # --- VINCOLI DI RIDONDANZA ---
    min_annotations_per_doc = models.IntegerField(
        default=3, 
        help_text="Target: How many people must annotate each document."
    )
    
    max_annotations_per_doc = models.IntegerField(
        default=5, 
        help_text="Hard Cap: Stop serving the document if it reaches this number (prevents waste)."
    )

    # Serve per dire: "Se un documento ha 2 annotazioni e gli altri 0, dai priorità a quelli con 0?"
    prioritize_unannotated = models.BooleanField(
        default=True,
        help_text="If True, the system will try to finish unannotated documents first."
    )

    dataset_file = models.FileField(
        upload_to='datasets/', 
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

    exclude_from_distribution = models.BooleanField(default=False)

    objects = models.Manager()

    def __str__(self):
        return f"{self.prolific_pid} (Consent: {self.consent_accepted})"


class ProjectEnrollment(models.Model):
    """
    Tracks the status of an annotator for a specific project (Screening/Training phase).
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='enrollments')
    annotator = models.ForeignKey(Annotator, on_delete=models.CASCADE, related_name='enrollments')
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'), # Not started or in progress
        ('PASSED', 'Passed'),   # Completed screening successfully
        ('FAILED', 'Failed'),   # Failed screening
    ]
    screening_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    
    # Survey responses
    survey_data = models.JSONField(default=dict, blank=True) 
    
    # Training Metrics
    training_tasks_completed = models.IntegerField(default=0)
    training_accuracy = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    
    class Meta:
        unique_together = ('project', 'annotator')

    def __str__(self):
        return f"{self.annotator} -> {self.project} ({self.screening_status})"


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