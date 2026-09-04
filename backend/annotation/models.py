from django.db import models
from django.core.exceptions import ValidationError

from django.db.models import JSONField 
from django.utils import timezone
import uuid
import os
from django.conf import settings
import yaml
from django.contrib.auth import get_user_model

def get_default_configuration_for_task_type():
    config_path = os.path.join(settings.BASE_DIR, 'resources', 'config_defaults', 'default_annotation_schema.yaml')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, IOError):
            pass
    return {
        "components": [
            {
                "type": "span_highlight",
                "labels": [
                    {
                    "name": "Actor",
                    "color": "#FF5733",
                    "hover_hint": "Who is allegedly responsible for a malicious action or agenda?"
                    },
                    {
                    "name": "Action",
                    "color": "#33FF57",
                    "hover_hint": "What is the actor doing or planning to do to cause negative outcomes?"
                    },
                    {
                    "name": "Victim",
                    "color": "#3357FF",
                    "hover_hint": "Who is negatively affected by the actor's agenda?"
                    },
                    {
                    "name": "Threat",
                    "color": "#FF33F6",
                    "hover_hint": "What is the actor doing or planning to do to cause negative outcomes?"
                    },
                    {
                    "name": "Evidence",
                    "color": "#FFA500",
                    "hover_hint": "Which arguments or expressions does the writer of the text use to support his claims?"
                    }
                ]
            },
            {
                "type": "classification",
                "options": [
                    { "label": "Conspiracy", "value": "Yes" },
                    { "label": "Not Conspiracy", "value": "No" },
                    { "label": "Ambiguous", "value": "Can't tell" }
                ]
            }
        ]
    }


def get_default_screening_config():
    config_path = os.path.join(settings.BASE_DIR, 'resources', 'config_defaults', 'default_screening_config.yaml')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, IOError):
            return []
    return [
        {"id": "age", "type": "number", "label": "How old are you?", "required": True, "min": 18, "max": 99},
        {"id": "gender", "type": "select", "label": "Gender?", "required": True, "options": ["Male", "Female", "Non-binary", "Prefer not to say"]},
        {"id": "native_language", "type": "text", "label": "Native language?", "required": True}
    ]

def get_default_configuration_for_informed_consent():
    config_path = os.path.join(settings.BASE_DIR, 'resources', 'config_defaults', 'default_informed_consent.md')

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError:
            pass

    return """
# Informed Consent

Welcome to the study! By clicking the button below, you confirm that you are at least 18 years old,
that you have read this information, and that you consent to participate.
    """

def get_default_codebook_content():
    config_path = os.path.join(settings.BASE_DIR, 'resources', 'config_defaults', 'codebook_item_similarity.md')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError:
            pass
    
    return """
            # Codebook

            ## Overview
            Describe the annotation task here. This content supports **Markdown** formatting.

            ## Definitions
            - **Label 1**: Description of label 1
            - **Label 2**: Description of label 2

            ## Examples
            Provide worked examples here to help annotators understand the task.

            ## Guidelines
            Any additional rules or edge cases the annotator should know.
        """

def get_default_instructions_content():
    config_path = os.path.join(settings.BASE_DIR, 'resources', 'config_defaults', 'default_instructions_content.md')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError:
            pass
    
    return """
        # Task Instructions

        ## The Goal
        Read the items and complete the annotation tasks as described in the codebook.

        ## How to Use the Interface
        1. Read the text carefully
        2. Select the appropriate classification
        3. Submit your annotation
    """

def get_default_practice_task():
    config_path = os.path.join(settings.BASE_DIR, 'resources', 'config_defaults', 'default_practice_task.yaml')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, IOError):
            pass
    
    return {}

class Project(models.Model):
    """
    Represents an annotation 'campaign' or 'batch'.
    Example: 'Sentiment Analysis Batch 1'
    """
    name = models.CharField(max_length=200, help_text="Project name")
    slug = models.SlugField(max_length=250, unique=True, blank=True, help_text="Unique Identifier for the URL (e.g., 'project-slug')")
    description = models.TextField(blank=True, help_text="Project description")
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('LIVE', 'Live'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='DRAFT',
        help_text="Current lifecycle state of the project."
    )
    is_published = models.BooleanField(
        default=False, 
        help_text="If True, the project is officially deployed. Configurations and datasets cannot be edited anymore."
    )
    
    launched_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the project was first set to LIVE.")

    def check_can_be_live(self):
        """
        Business logic: a project CANNOT be LIVE if it has no documents to annotate.
        Raises ValidationError if conditions are not met.
        """
        if self.status == 'LIVE':
            # Use getattr to avoid lint errors for reverse/dynamic relationships defined later
            docs_manager = getattr(self, 'documents', None)
            has_docs = docs_manager.filter(is_gold_unit=False).exists() if docs_manager else False
            if not has_docs and not self.documents_file:
                raise ValidationError(
                    "❌ Cannot Set to LIVE: No dataset found. "
                    "Please upload a .jsonl file before setting the project status to Live."
                )

    def save(self, *args, **kwargs):
        # 1. Basic slug generation
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        
        # 2. Validation: check if it can be set to LIVE
        # (Skip for new objects if they don't have a PK yet, but usually we handle this in the form)
        if self.pk:
            self.check_can_be_live()

        # 3. Launch timestamp management
        if not self.pk:
            if self.status == 'LIVE':
                self.launched_at = timezone.now()
        else:
            old_instance = Project.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                if self.status == 'LIVE' and not self.launched_at:
                    self.launched_at = timezone.now()

        super().save(*args, **kwargs)

    @property
    def can_accept_annotations(self):
        return self.status == 'LIVE'
    
    # CONFIGURATION
    
    informed_consent_config = models.TextField(
        default=get_default_configuration_for_informed_consent, 
        help_text="Informed Consent Configuration: accept a string can be showed to the annotator before starting the task"
    )
    
    annotation_schema = models.JSONField(
        default=get_default_configuration_for_task_type,
        help_text="Annotation schema (span labels, class labels, colors)"
    )

    # --- QUALITY CONTROL / GOLD UNITS ---
    enable_gold_units = models.BooleanField(
        default=False,
        help_text="If True, gold units will be injected for quality control during annotation."
    )

    min_accuracy_required = models.FloatField(
        default=0.6, 
        help_text="Minimum accuracy required for gold tasks (0.0 to 1.0)."
    )
    
    gold_injection_frequency = models.IntegerField(
        default=5, 
        help_text="Frequency of gold task injection (e.g., 1 every 5 tasks)."
    )
    
    min_gold_before_eval = models.IntegerField(
        default=3, 
        help_text="Min gold units completed before starting evaluation."
    )
    
    gold_units_file = models.FileField(
        upload_to='datasets/gold/', 
        null=True,
        blank=True,
        help_text="Upload a .jsonl file for GOLD units (Quality Control Injection)."
    )

    # --- TOGGLE SWITCHES ---
    enable_screening = models.BooleanField(
        default=False,
        help_text="If True, annotators will see the screening questionnaire before the task."
    )

    screening_config = models.JSONField(
        default=get_default_screening_config,
        blank=True,
        help_text="Screening questionnaire: JSON list of questions shown to annotators before the task. Empty list = skip screening."
    )

    # --- CODEBOOK (THEORETICAL-PRACTICAL BACKGROUND) ---
    enable_codebook = models.BooleanField(
        default=False,
        help_text="If True, annotators will see the codebook/instructions before the task."
    )
    
    codebook_content = models.TextField(
        default=get_default_codebook_content,
        blank=True,
        help_text="Codebook content in Markdown format. Shown to annotators as theoretical/practical background."
    )

    # --- INSTRUCTIONS / ONBOARDING ---
    enable_instructions = models.BooleanField(
        default=False,
        help_text="If True, annotators will see task instructions and optional practice task before annotating."
    )

    instructions_content = models.TextField(
        default=get_default_instructions_content,
        blank=True,
        help_text="Instructions content in Markdown format. Shown to annotators as task instructions before the practice."
    )

    enable_practice_task = models.BooleanField(
        default=False,
        help_text="If True, annotators will see a practice task before starting the real task."
    )

    practice_task_config = models.JSONField(
        default=get_default_practice_task,
        blank=True,
        help_text="Practice task config: { text, gold_solution: {classification, spans[]}, hints[] }. Empty = no practice."
    )

    practice_task_required = models.BooleanField(
        default=False,
        help_text="If True, annotators must pass the practice task correctly before starting. If False, they can skip after attempting."
    )

    # --- DISTRIBUTION CONSTRAINTS ---

    prolific_completion_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="The code provided by Prolific to confirm completion. Participants will be redirected to Prolific with this code."
    )

    STRATEGY_CHOICES = [
        ('STANDARD', 'Standard - Randomly assign documents to annotators'),
        ('FULL_OVERLAP', 'Everyone sees everything (High Redundancy) - All annotators see all documents'),
        ('SAME_ANNOTATORS', 'Same k annotators view the same document (Low Redundancy) - the annotators are assigned to blocks of documents')
    ]
    
    distribution_strategy = models.CharField(
        max_length=20, 
        choices=STRATEGY_CHOICES, 
        default='STANDARD',
        help_text="Defines how documents are assigned to annotators."
    )

    min_annotations_per_doc = models.IntegerField(
        default=3, 
        help_text="Target: How many people must annotate each document."
    )
    
    max_annotations_per_doc = models.IntegerField(
        default=5, 
        help_text="Hard Cap: Stop serving the document if it reaches this number (prevents waste)."
    )

    # If a document has 2 annotations and others have 0, should unannotated ones be prioritized?
    prioritize_unannotated = models.BooleanField(
        default=True,
        help_text="If True, the system will try to finish unannotated documents first."
    )

    # BLOCK SETTINGS FOR SAME_ANNOTATORS
    block_size = models.IntegerField(
        default=10,
        help_text="SAME_ANNOTATORS strategy: Number of documents injected into each block."
    )
    
    annotators_per_block = models.IntegerField(
        default=3,
        help_text="SAME_ANNOTATORS strategy: Number of distinct annotators assigned to each block."
    )

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

    documents_file = models.FileField(
        upload_to='datasets/documents/',
        blank=True,
        null=True, 
        help_text="Upload a .jsonl file for REAL documents to be annotated."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='owned_projects',
        help_text="The staff user who created and owns this project."
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ProjectMembership',
        related_name='member_projects',
        blank=True,
    )

    objects = models.Manager()

    def __str__(self):
        return self.name


class ProjectMembership(models.Model):
    """
    Links a Django staff user to a project as a collaborator.
    The owner is also stored here (role='OWNER') for unified querying.
    """
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),
        ('COLLABORATOR', 'Collaborator'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='COLLABORATOR')
    added_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        unique_together = ('project', 'user')
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"

    def __str__(self):
        return f"{self.user} → {self.project} ({self.role})"


class ProjectLogEntry(models.Model):
    """
    Tracks significant events in a project's lifecycle.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=100, help_text="The event type (e.g., 'Project Launched', 'Status Changed', 'Data Imported')")
    details = models.TextField(blank=True, help_text="Optional details or message.")
    
    objects = models.Manager()
    
    class Meta:
        verbose_name = "Project Log Entry"
        verbose_name_plural = "Project Log Entries"
        ordering = ['-timestamp']

    def __str__(self):
        if self.timestamp:
            from django.utils import dateformat
            return f"[{dateformat.format(self.timestamp, 'Y-m-d H:i')}] {self.action}"
        return f"[No Date] {self.action}"

class Annotator(models.Model):
    prolific_pid = models.CharField(max_length=255, unique=True, db_index=True)
    is_test = models.BooleanField(default=False, help_text="If True, this is a test/admin session and should be excluded from metrics.")
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = JSONField(default=dict, blank=True)
    
    objects = models.Manager()

    def __str__(self):
        return f"{self.prolific_pid}"

class ProjectEnrollment(models.Model):
    """
    Tracks the status of an annotator for a specific project (Screening/Training phase).
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='enrollments')
    annotator = models.ForeignKey(Annotator, on_delete=models.CASCADE, related_name='enrollments')
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),       # Pre-annotation phases not completed
        ('ACTIVE', 'Active'),         # Annotating documents
        ('EXCLUDED', 'Excluded'),     # Removed for low quality
        ('COMPLETED', 'Completed'),   # Target tasks reached
    ]

    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        help_text="PENDING = pre-task phases incomplete. ACTIVE = annotating. EXCLUDED = low quality. COMPLETED = done."
    )
    
    # Gold Unit Quality Metrics
    gold_tasks_completed = models.IntegerField(default=0)
    gold_accuracy = models.FloatField(null=True, blank=True)
    gold_strikes = models.IntegerField(default=0, help_text="Consecutive wrong gold answers (for strike-based evaluation).")
    
    # Per-project phase tracking
    consent_accepted = models.BooleanField(default=False)
    screening_completed = models.BooleanField(default=False)
    codebook_completed = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)
    
    exclude_from_distribution = models.BooleanField(default=False)
    
    assigned_block_id = models.IntegerField(null=True, blank=True, help_text="The document block assigned to this annotator (for SAME_ANNOTATORS).")
    
    # MACE Quality Estimation
    mace_competence_score = models.FloatField(null=True, blank=True, help_text="MACE estimated reliability (0.0 to 1.0)")
    mace_spam_bias = models.JSONField(default=dict, blank=True, help_text="Estimated bias distribution when guessing")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    
    class Meta:
        unique_together = ('project', 'annotator')
        verbose_name = "Enrollment & Assignment"
        verbose_name_plural = "Enrollments & Assignments"

    def __str__(self):
        return f"{self.annotator} -> {self.project} ({self.status})"

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
    text = models.TextField()
    
    # External ID (e.g. ID from the original dataset)
    external_id = models.CharField(max_length=100, blank=True, null=True)

    # Metadata for context (e.g., {"subreddit": "conspiracy", "thread_id": "..."})
    metadata = JSONField(default=dict, blank=True)
    
    # GOLD UNITS MANAGEMENT (Quality Control)
    # If True, this document has a known correct answer and is used for injection.
    is_gold_unit = models.BooleanField(default=False)
    # The correct answer (in JSON format) for automatic comparison
    gold_solution = JSONField(default=dict, blank=True, null=True)

    # MACE Inference Results
    mace_gold_label = models.CharField(max_length=50, null=True, blank=True)
    mace_confidence = models.FloatField(null=True, blank=True, help_text="Certainty of the MACE prediction (entropy)")

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

    # GROUPING/BLOCK FOR 'SAME_ANNOTATORS' STRATEGY
    block_id = models.IntegerField(null=True, blank=True, db_index=True, help_text="Used to group documents into blocks for the SAME_ANNOTATORS strategy")

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
    
    is_test = models.BooleanField(default=False, help_text="If True, this annotation was made in test mode.")
    
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        # An annotator cannot annotate the same document twice, the DB will raise an error if they try.
        unique_together = ('document', 'annotator')

    def __str__(self):
        return f"Annotation {self.id} by {self.annotator}"

class DocumentProxy(Document):
    """Proxy model for standard Documents."""
    class Meta:
        proxy = True
        verbose_name = "Annotation Document"
        verbose_name_plural = "Annotation Documents"
        default_permissions = ('add', 'change', 'delete', 'view')

class GoldUnitProxy(Document):
    """Proxy model for Quality Control Units (Gold Injection)."""
    class Meta:
        proxy = True
        verbose_name = "Gold Unit"
        verbose_name_plural = "Gold Units"
        default_permissions = ('add', 'change', 'delete', 'view')