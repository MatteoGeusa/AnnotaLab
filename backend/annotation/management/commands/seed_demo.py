"""
Django Management Command: seed_demo
-------------------------------------
Creates two demo projects:
  1. PROJECT_DRAFT  - ready to be configured, status=DRAFT
  2. PROJECT_LIVE   - active, with documents, annotators and annotations

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --flush   # deletes all existing demo data first
"""

import random
import uuid
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from annotation.models import (
    Project, Document, Annotator, Annotation,
    ProjectEnrollment, ProjectLogEntry
)

# ---------------------------------------------------------------------------
# Sample texts (short conspiracy-style sentences for demo)
# ---------------------------------------------------------------------------
SAMPLE_TEXTS = [
    "Scientists claim that 5G towers are designed to suppress the immune system of the population.",
    "A leaked document reveals that the moon landing was staged in a Hollywood studio.",
    "The government adds fluoride to water supplies to make people docile and easier to control.",
    "Big Pharma is hiding the cure for cancer to keep profits from chemotherapy treatments high.",
    "Chemtrails left by aircraft are actually chemical agents used to manipulate the weather.",
    "The Illuminati controls world governments through a network of secret societies.",
    "Microchips hidden in vaccines are used to track and monitor every citizen.",
    "The media blackout on this story proves that someone powerful wants it suppressed.",
    "A whistleblower revealed that elections are rigged through voting machine software.",
    "Ancient pyramids were built by an advanced alien civilization, not humans.",
    "Banks create money out of thin air and charge interest to enslave entire nations.",
    "The deep state orchestrates terror attacks to justify expanding surveillance powers.",
    "A secret cabal of elites meets annually to decide the fate of world economies.",
    "Satellites in orbit are actually weapons platforms disguised as communication relays.",
    "The real flat earth is hidden behind an Antarctic ice wall guarded by the military.",
    "COVID-19 was engineered in a laboratory as a population control mechanism.",
    "The federal reserve is a private bank that profits from wars it secretly funds.",
    "Reptilian shapeshifters have infiltrated the highest levels of government worldwide.",
    "Mind control signals are broadcast through television sets during prime time hours.",
    "The cure for Alzheimer's was discovered decades ago but suppressed by pharmaceutical companies.",
]

GOLD_TEXTS = [
    {
        "text": "The government is putting chips in the water to control us and nobody seems to care.",
        "gold_solution": {
            "classification": "Yes",
            "spans": [
                {"start": 0, "end": 14, "label": "Actor", "text": "The government"},
                {"start": 18, "end": 47, "label": "Action", "text": "putting chips in the water to"},
                {"start": 48, "end": 58, "label": "Victim", "text": "control us"},
            ]
        }
    },
    {
        "text": "This article is simply reporting on record rainfall levels observed this month.",
        "gold_solution": {
            "classification": "No",
            "spans": []
        }
    },
]

# Classification labels for fake annotations
LABELS = ["Yes", "No", "Can't tell"]

TASK_CONFIG = {
    "question": "Does this text describe or promote a conspiracy theory?",
    "instruction": "Read the text carefully and: (1) highlight the key elements using the span labels, (2) select the overall classification.",
    "components": [
        {
            "type": "span_highlight",
            "labels": [
                {"name": "Actor", "color": "#ef4444", "hover_hint": "Who is responsible?"},
                {"name": "Action", "color": "#f59e0b", "hover_hint": "What did they do?"},
                {"name": "Target", "color": "#3b82f6", "hover_hint": "Who is the victim?"}
            ]
        },
        {
            "type": "classification",
            "options": [
                {"label": "Conspiracy", "value": "Yes"},
                {"label": "Not Conspiracy", "value": "No"},
                {"label": "Ambiguous", "value": "Can't tell"}
            ]
        }
    ]
}

# Gold Default Values for Demo
DEMO_GOLD_SETTINGS = {
    "min_accuracy_required": 0.6,
    "gold_injection_frequency": 5,
    "min_gold_before_eval": 2
}


class Command(BaseCommand):
    help = "Seeds the database with demo projects for development/presentation."

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing demo projects before creating new ones.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        self.stdout.write(self.style.WARNING("\n🌱 Seeding demo data...\n"))
        self._create_draft_project()
        self._create_live_project()
        self.stdout.write(self.style.SUCCESS("\n✅ Done! Demo data created successfully.\n"))

    # -----------------------------------------------------------------------
    def _flush(self):
        self.stdout.write("🗑️  Flushing existing demo projects...")
        Project.objects.filter(slug__startswith="demo-").delete()
        Annotator.objects.filter(prolific_pid__startswith="DEMO_").delete()
        self.stdout.write(self.style.SUCCESS("   Flush complete.\n"))

    # -----------------------------------------------------------------------
    def _create_draft_project(self):
        self.stdout.write("📋 Creating DRAFT project...")

        project, created = Project.objects.get_or_create(
            slug="demo-draft-study",
            defaults={
                "name": "[DEMO] Climate Narratives Study",
                "description": (
                    "A study examining how conspiracy narratives appear in online discussions "
                    "about climate change. This project is configured but not yet launched."
                ),
                "status": "DRAFT",
                "annotation_schema": TASK_CONFIG,
                "min_accuracy_required": DEMO_GOLD_SETTINGS["min_accuracy_required"],
                "gold_injection_frequency": DEMO_GOLD_SETTINGS["gold_injection_frequency"],
                "min_gold_before_eval": DEMO_GOLD_SETTINGS["min_gold_before_eval"],
                "enable_gold_units": True,
                "enable_screening": True,
                "enable_codebook": True,
                "enable_instructions": True,
                "enable_practice_task": True,
                "distribution_strategy": "STANDARD",
                "min_annotations_per_doc": 3,
                "max_annotations_per_doc": 5,
                "prioritize_unannotated": True,
                "dataset_text_key": "text",
                "dataset_id_key": "_id",
                "documents_file": "",
            }
        )

        if not created:
            self.stdout.write(self.style.WARNING("   ⚠️  Draft project already exists, skipping."))
            return

        # Add a few draft documents (not yet live)
        for i, text in enumerate(SAMPLE_TEXTS[:5]):
            Document.objects.create(
                project=project,
                text=text,
                external_id=f"DRAFT_DOC_{i+1:03d}",
                metadata={"source": "demo", "batch": "draft"},
                is_gold_unit=False,
                min_annotations_required=3,
            )

        # Log
        ProjectLogEntry.objects.create(
            project=project,
            action="Project Created",
            details="[DEMO] Draft project initialized with 5 sample documents."
        )

        self.stdout.write(self.style.SUCCESS(
            f"   ✅ '{project.name}' created (DRAFT, 5 documents, not launched)"
        ))

    # -----------------------------------------------------------------------
    def _create_live_project(self):
        self.stdout.write("🟢 Creating LIVE project with annotations...")

        project, created = Project.objects.get_or_create(
            slug="demo-live-conspiracy",
            defaults={
                "name": "[DEMO] Conspiracy Theory Detection",
                "description": (
                    "Active annotation campaign for detecting conspiracy theories in social media posts. "
                    "Annotators highlight key spans and classify each post."
                ),
                "status": "LIVE",
                "launched_at": timezone.now(),
                "annotation_schema": TASK_CONFIG,
                "min_accuracy_required": DEMO_GOLD_SETTINGS["min_accuracy_required"],
                "gold_injection_frequency": DEMO_GOLD_SETTINGS["gold_injection_frequency"],
                "min_gold_before_eval": DEMO_GOLD_SETTINGS["min_gold_before_eval"],
                "enable_gold_units": True,
                "enable_screening": True,
                "enable_codebook": True,
                "enable_instructions": True,
                "enable_practice_task": True,
                "distribution_strategy": "STANDARD",
                "min_annotations_per_doc": 3,
                "max_annotations_per_doc": 5,
                "prioritize_unannotated": True,
                "dataset_text_key": "text",
                "dataset_id_key": "_id",
                "documents_file": "",
            }
        )

        if not created:
            self.stdout.write(self.style.WARNING("   ⚠️  Live project already exists, skipping."))
            return

        # --- Create regular documents ---
        docs = []
        for i, text in enumerate(SAMPLE_TEXTS):
            doc = Document.objects.create(
                project=project,
                text=text,
                external_id=f"LIVE_DOC_{i+1:03d}",
                metadata={"source": "reddit", "subreddit": random.choice(["conspiracy", "worldnews", "science"])},
                is_gold_unit=False,
                min_annotations_required=3,
            )
            docs.append(doc)

        # --- Create gold units ---
        gold_docs = []
        for i, g in enumerate(GOLD_TEXTS):
            gdoc = Document.objects.create(
                project=project,
                text=g["text"],
                external_id=f"LIVE_GOLD_{i+1:03d}",
                metadata={"source": "gold"},
                is_gold_unit=True,
                gold_solution=g["gold_solution"],
                min_annotations_required=3,
            )
            gold_docs.append(gdoc)

        # --- Create fake annotators ---
        annotator_specs = [
            {"pid": "DEMO_EXPERT_001",  "accuracy": 0.95, "n_docs": 18, "status": "ACTIVE"},
            {"pid": "DEMO_EXPERT_002",  "accuracy": 0.90, "n_docs": 15, "status": "ACTIVE"},
            {"pid": "DEMO_AVERAGE_001", "accuracy": 0.70, "n_docs": 12, "status": "ACTIVE"},
            {"pid": "DEMO_AVERAGE_002", "accuracy": 0.65, "n_docs": 10, "status": "ACTIVE"},
            {"pid": "DEMO_SPAMMER_001", "accuracy": 0.30, "n_docs":  8, "status": "EXCLUDED"},
            {"pid": "DEMO_NEW_001",     "accuracy": 0.80, "n_docs":  2, "status": "ACTIVE"},
        ]

        annotators = []
        for spec in annotator_specs:
            pid = spec["pid"]
            accuracy = spec["accuracy"]
            n_docs = spec["n_docs"]
            status = spec["status"]

            ann, _ = Annotator.objects.get_or_create(
                prolific_pid=pid,
                defaults={
                    "consent_accepted": True,
                    "screening_completed": True,
                    "onboarding_completed": True,
                    "metadata": {"source": "demo", "reliability": accuracy},
                }
            )
            annotators.append((ann, spec))

            # Enrollment
            gold_tasks = 1 if n_docs >= 5 else 0  # type: ignore[unsupported-operator]
            gold_acc = accuracy if n_docs >= 5 else None  # type: ignore[unsupported-operator]

            ProjectEnrollment.objects.get_or_create(
                project=project,
                annotator=ann,
                defaults={
                    "status": status,
                    "gold_tasks_completed": gold_tasks,
                    "gold_accuracy": gold_acc,
                    "codebook_completed": True,
                }
            )

        # --- Create fake annotations ---
        annotation_count = 0
        for ann, spec in annotators:
            # Pick a random subset of docs this annotator has already annotated
            subset = random.sample(docs, min(spec["n_docs"], len(docs)))
            for doc in subset:
                # Skip if already annotated (unique_together constraint)
                if Annotation.objects.filter(document=doc, annotator=ann).exists():
                    continue

                # Expert annotators give correct-ish labels, spammers give random ones
                if spec["accuracy"] > 0.6:
                    label = random.choices(LABELS, weights=[0.6, 0.3, 0.1])[0]
                else:
                    label = random.choice(LABELS)

                result = {"classification": label, "spans": []}

                Annotation.objects.create(
                    document=doc,
                    annotator=ann,
                    result=result,
                    milliseconds_to_complete=random.randint(8000, 45000),
                )
                doc.current_annotations_count += 1
                doc.save(update_fields=["current_annotations_count"])
                annotation_count += 1

        # --- Log lifecycle events ---
        ProjectLogEntry.objects.create(
            project=project,
            action="Project Created",
            details="[DEMO] Live project initialized."
        )
        ProjectLogEntry.objects.create(
            project=project,
            action="Dataset Imported",
            details=f"Successfully imported {len(docs)} regular documents and {len(gold_docs)} gold units."
        )
        ProjectLogEntry.objects.create(
            project=project,
            action="Status Changed",
            details="Project changed from DRAFT to LIVE."
        )

        total_annotators = len(annotators)
        self.stdout.write(self.style.SUCCESS(
            f"   ✅ '{project.name}' created:\n"
            f"      - Status: LIVE\n"
            f"      - Documents: {len(docs)} regular + {len(gold_docs)} gold units\n"
            f"      - Annotators: {total_annotators} ({sum(1 for _, s in annotators if s['status'] == 'ACTIVE')} active, "
            f"{sum(1 for _, s in annotators if s['status'] == 'EXCLUDED')} excluded)\n"
            f"      - Annotations created: {annotation_count}\n"
            f"      - Admin link: http://localhost:8000/admin/annotation/project/{project.id}/change/"
        ))
