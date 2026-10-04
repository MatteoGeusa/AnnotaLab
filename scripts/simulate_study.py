"""
Full end-to-end study simulation.

Creates a realistic annotation study (20 documents + 5 gold units, 10 annotators
with different competence profiles) and drives every annotator through the REAL
API endpoints: session -> consent -> screening -> codebook -> instructions ->
onboarding -> next-task/submit loop, including gold injection and automatic
exclusion. Finally runs MACE and prints a full report.
"""
import random
import datetime

from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from annotation.models import (
    Project, Document, Annotator, Annotation, ProjectEnrollment, ProjectLogEntry
)

random.seed(2026)

PROJECT_NAME = "Conspiracy Narrative Detection - Wave 1"
PROJECT_SLUG = "conspiracy-wave-1"

# ---------------------------------------------------------------- 1. CLEANUP
existing = Project.objects.filter(slug=PROJECT_SLUG).first()
if existing:
    Annotation.objects.filter(document__project=existing).delete()
    pids = list(ProjectEnrollment.objects.filter(project=existing).values_list('annotator__prolific_pid', flat=True))
    ProjectEnrollment.objects.filter(project=existing).delete()
    Annotator.objects.filter(prolific_pid__in=pids).delete()
    Document.objects.filter(project=existing).delete()
    existing.delete()
    print(f"Removed previous '{PROJECT_SLUG}' project.")

# ------------------------------------------------------------- 2. THE SCHEMA
ANNOTATION_SCHEMA = {
    "components": [
        {
            "type": "span_highlight",
            "labels": [
                {"name": "Actor", "color": "#FF5733", "hover_hint": "Who is allegedly responsible?"},
                {"name": "Action", "color": "#33FF57", "hover_hint": "What are they doing?"},
                {"name": "Victim", "color": "#3357FF", "hover_hint": "Who is harmed?"},
                {"name": "Threat", "color": "#FF33F6", "hover_hint": "What is the feared outcome?"},
                {"name": "Evidence", "color": "#FFA500", "hover_hint": "What is cited as proof?"},
            ],
        },
        {
            "type": "classification",
            "question": "Is this text promoting a conspiracy narrative?",
            "multi_select": False,
            "options": [
                {"label": "Conspiracy", "value": "Yes"},
                {"label": "Not Conspiracy", "value": "No"},
                {"label": "Ambiguous", "value": "Can't tell"},
            ],
        },
    ]
}

SCREENING_CONFIG = [
    {"id": "age_range", "label": "What is your age range?", "type": "select", "required": True,
     "options": ["18-24", "25-34", "35-44", "45-54", "55+"]},
    {"id": "native_english", "label": "Are you a native English speaker?", "type": "select", "required": True,
     "options": ["Yes", "No"]},
    {"id": "education", "label": "Highest level of education completed", "type": "select", "required": True,
     "options": ["High school", "Bachelor", "Master", "PhD"]},
    {"id": "social_media_use", "label": "How often do you use social media?", "type": "select", "required": False,
     "options": ["Daily", "Weekly", "Rarely", "Never"]},
]

CODEBOOK = """# Codebook - Conspiracy Narrative Detection

## Definition
A **conspiracy narrative** claims that a secret, powerful group is deliberately
causing harm or hiding the truth from the public.

## Core elements
1. **Actor** - a group acting in secret (government, corporations, elites)
2. **Action** - a deliberate, coordinated, hidden plan
3. **Victim** - the deceived or harmed public
4. **Threat** - the harmful outcome
5. **Evidence** - what the author presents as proof

## Decision rules
- Mere criticism of institutions is **not** a conspiracy narrative.
- Reporting on a real, documented conspiracy is **not** a conspiracy narrative.
- If secrecy and intent are implied but not asserted, use **Ambiguous**.
"""

INSTRUCTIONS = """# Task Instructions

For each text you will:

1. **Highlight** the narrative elements you can identify (Actor, Action, Victim,
   Threat, Evidence). Not every text contains all of them.
2. **Classify** the text as *Conspiracy*, *Not Conspiracy* or *Ambiguous*.

Work carefully: a subset of the items has a known correct answer and is used to
monitor annotation quality.
"""

PRACTICE_TASK = {
    "text": "They keep telling us the new power plant is safe, but nobody has seen the inspection reports. Make your own conclusions.",
    "gold_solution": {"classification": "Can't tell"},
    "hints": [
        "Secrecy is implied ('nobody has seen the reports') but no coordinated secret plan is asserted.",
        "When intent is hinted but not claimed, the answer is Ambiguous.",
    ],
}

# ----------------------------------------------------------- 3. THE DATASET
# (text, hidden_true_label) - the label the study designer considers correct.
REGULAR_DOCS = [
    ("The city council approved the new bus routes after three public hearings. Ridership data from the pilot program was published on the transit authority website.", "No"),
    ("They are putting chemicals in the water supply to keep the population docile. Why else would every official refuse to release the full treatment reports?", "Yes"),
    ("A study published in The Lancet reports a 12% reduction in hospital admissions following the vaccination campaign in the region.", "No"),
    ("Big pharma has known about the side effects for decades. The FDA approval process is just a formality once the donations clear.", "Yes"),
    ("The unemployment figures were revised downward for the third quarter, according to the national statistics office.", "No"),
    ("Funny how the power went out in exactly the three districts where the recount was happening. Coincidence? I'll let you decide.", "Yes"),
    ("I am not saying it was planned, but the timing of the announcement right before the vote was certainly convenient for them.", "Can't tell"),
    ("Local farmers reported lower yields this season due to the extended drought, consistent with regional climate projections.", "No"),
    ("The banking elites engineered the 2008 collapse to consolidate assets. It is all documented if you know where to look.", "Yes"),
    ("Scientists at the institute published their raw data alongside the paper so other labs could replicate the experiment.", "No"),
    ("Every single mainstream outlet ran the identical headline within twenty minutes. That is not journalism, that is coordination.", "Yes"),
    ("The minister resigned following the parliamentary inquiry into the procurement contracts.", "No"),
    ("Some people are asking questions about the trial data and they get banned instantly. Draw your own conclusions about who benefits.", "Yes"),
    ("The bridge inspection found structural fatigue in two support columns; repairs are scheduled for spring.", "No"),
    ("Watergate proved that governments do conspire. So it is not paranoid to ask what they are hiding right now.", "Can't tell"),
    ("Researchers disclosed a funding conflict of interest in the acknowledgements section of the study.", "No"),
    ("The surveillance program was revealed through leaked documents and later confirmed in court filings.", "No"),
    ("They replaced the school curriculum overnight to condition the children. Parents were never consulted because compliance was the goal.", "Yes"),
    ("It seems odd that the report was delayed twice, though the agency says it was a staffing issue.", "Can't tell"),
    ("Quarterly earnings missed analyst expectations, and the company attributed the shortfall to supply chain delays.", "No"),
]

# Gold units: unambiguous items, using the schema VALUES (not the labels).
GOLD_DOCS = [
    ("A secret cabal of billionaires controls every government on earth and stages every crisis to tighten their grip on humanity.", "Yes"),
    ("The national weather service published its monthly rainfall averages for the last ten years in an open data portal.", "No"),
    ("Doctors are paid to hide the real cure. The entire medical establishment is in on it and they silence anyone who speaks up.", "Yes"),
    ("The train timetable will change on Monday to accommodate scheduled track maintenance between the two stations.", "No"),
    ("They faked the entire landing in a studio and every photograph since has been manufactured to maintain the lie.", "Yes"),
]

# ------------------------------------------------------- 4. CREATE PROJECT
User = get_user_model()
owner = User.objects.filter(is_superuser=True).first()

project = Project.objects.create(
    name=PROJECT_NAME,
    slug=PROJECT_SLUG,
    description=(
        "Wave 1 of a crowdsourced study on the detection of conspiracy narratives in "
        "social media posts. Each item is annotated by multiple workers; gold units "
        "are injected for quality control and MACE is used to estimate annotator competence."
    ),
    status='DRAFT',
    owner=owner,
    annotation_schema=ANNOTATION_SCHEMA,
    # pre-task phases: the full pipeline
    enable_screening=True,
    screening_config=SCREENING_CONFIG,
    enable_codebook=True,
    codebook_content=CODEBOOK,
    enable_instructions=True,
    instructions_content=INSTRUCTIONS,
    enable_practice_task=True,
    practice_task_config=PRACTICE_TASK,
    practice_task_required=False,
    # quality control
    enable_gold_units=True,
    gold_injection_frequency=4,
    min_gold_before_eval=3,
    min_accuracy_required=0.6,
    # distribution
    distribution_strategy='STANDARD',
    min_annotations_per_doc=3,
    max_annotations_per_doc=5,
    prioritize_unannotated=True,
    prolific_completion_code="C1WAVE26",
)

hidden_truth = {}
for i, (text, truth) in enumerate(REGULAR_DOCS, start=1):
    doc = Document.objects.create(
        project=project, text=text, external_id=f"D-{i:03d}",
        metadata={"source": "reddit", "batch": "wave1"},
        is_gold_unit=False, gold_solution=None,
        min_annotations_required=project.min_annotations_per_doc,
    )
    hidden_truth[doc.id] = truth

for i, (text, truth) in enumerate(GOLD_DOCS, start=1):
    Document.objects.create(
        project=project, text=text, external_id=f"G-{i:03d}",
        metadata={"source": "curated", "batch": "wave1-gold"},
        is_gold_unit=True, gold_solution={"classification": truth},
        min_annotations_required=project.min_annotations_per_doc,
    )

ProjectLogEntry.objects.create(project=project, action="Project Created",
                               details=f"Project '{project.name}' initialized.")
ProjectLogEntry.objects.create(project=project, action="Dataset Imported",
                               details=f"Imported {len(REGULAR_DOCS)} documents and {len(GOLD_DOCS)} gold units.")

project.status = 'LIVE'
project.is_published = True
project.save()
ProjectLogEntry.objects.create(project=project, action="Project Launched",
                               details="Wave 1 opened to Prolific participants.")

print(f"Created project '{project.name}' (slug={project.slug}, id={project.id})")
print(f"  {len(REGULAR_DOCS)} documents + {len(GOLD_DOCS)} gold units, published={project.is_published}")

# ------------------------------------------------------ 5. THE ANNOTATORS
# (pid, profile, accuracy, session_length, always_answer)
WORKERS = [
    ("5f2a91c4e8b07a3d19c4e011", "expert",  0.95, 20, None),
    ("6a13b7d2c9e04f8a27d1b022", "expert",  0.92, 18, None),
    ("7b24c8e3d0f15a9b38e2c033", "expert",  0.90, 17, None),
    ("8c35d9f4e1026bac49f3d044", "good",    0.82, 16, None),
    ("9d46e0a5f2137cbd50a4e055", "good",    0.80, 19, None),
    ("0e57f1b603248dce61b5f066", "good",    0.78, 14, None),
    ("1f68a2c714359edf72c60077", "average", 0.65, 15, None),
    ("2a79b3d825460fe083d71088", "sloppy",  0.30, 16, None),
    ("3b80c4e936571af194e82099", "sloppy",  0.25, 13, None),
    ("4c91d5fa47682b0a5f930aa1", "spammer", 0.00, 12, "Yes"),
]

CLASSES = ["Yes", "No", "Can't tell"]
COUNTRIES = ["United Kingdom", "Italy", "Poland", "Portugal", "Spain", "Greece", "Germany"]
DEVICES = ["desktop", "laptop", "tablet"]
AGES = ["18-24", "25-34", "35-44", "45-54", "55+"]
EDU = ["High school", "Bachelor", "Master", "PhD"]
SPAN_LABELS = ["Actor", "Action", "Victim", "Threat", "Evidence"]


def make_spans(text, profile):
    """Produce plausible span annotations; weaker workers highlight less."""
    n = {"expert": 3, "good": 2, "average": 2, "sloppy": 1, "spammer": 0}[profile]
    words = text.split()
    spans = []
    for _ in range(min(n, max(0, len(words) // 6))):
        start_word = random.randrange(0, max(1, len(words) - 4))
        length = random.randint(2, 4)
        fragment = " ".join(words[start_word:start_word + length])
        start = text.find(fragment)
        if start == -1:
            continue
        spans.append({
            "start": start,
            "end": start + len(fragment),
            "label": random.choice(SPAN_LABELS),
            "text": fragment,
        })
    return spans


def answer_for(true_label, accuracy, always):
    if always:
        return always
    if true_label and random.random() < accuracy:
        return true_label
    return random.choice(CLASSES)


# ------------------------------------------------------- 6. RUN THE FLOW
client = Client()
report_rows = []

URL_SESSION = reverse('session')
URL_CONSENT = reverse('consent')
URL_GET_SCREENING = reverse('get_screening')
URL_SCREENING = reverse('screening')
URL_GET_CODEBOOK = reverse('get_codebook')
URL_CODEBOOK = reverse('codebook')
URL_GET_INSTRUCTIONS = reverse('get_instructions')
URL_ONBOARDING = reverse('onboarding')
URL_NEXT = reverse('next_task')
URL_SUBMIT = reverse('submit')

now = timezone.now()
sim_start = now - datetime.timedelta(days=6)

state = {}

with override_settings(ALLOWED_HOSTS=['*']):
    # --- Phase 1: every worker goes through the onboarding funnel ---
    for pid, profile, accuracy, session_len, always in WORKERS:
        base = {"prolific_pid": pid, "project_slug": PROJECT_SLUG}

        client.post(URL_SESSION, {**base, "metadata": {
            "country": random.choice(COUNTRIES),
            "device": random.choice(DEVICES),
            "study_id": "wave-1",
        }}, content_type="application/json")

        client.post(URL_CONSENT, base, content_type="application/json")

        client.get(URL_GET_SCREENING, base)
        client.post(URL_SCREENING, {**base, "responses": {
            "age_range": random.choice(AGES),
            "native_english": random.choice(["Yes", "No"]),
            "education": random.choice(EDU),
            "social_media_use": random.choice(["Daily", "Weekly", "Rarely"]),
        }}, content_type="application/json")

        client.get(URL_GET_CODEBOOK, base)
        client.post(URL_CODEBOOK, base, content_type="application/json")

        client.get(URL_GET_INSTRUCTIONS, base)
        client.post(URL_ONBOARDING, base, content_type="application/json")

        state[pid] = {
            "base": base, "profile": profile, "accuracy": accuracy,
            "session_len": session_len, "always": always,
            "seq": [], "ann_ids": [], "stop": "session_limit", "active": True,
            "start": sim_start + datetime.timedelta(hours=random.randint(0, 72)),
        }

    print("  All 10 workers completed consent / screening / codebook / instructions.")

    # --- Phase 2: workers annotate CONCURRENTLY (round-robin) ---
    tick = 0
    while any(s["active"] for s in state.values()):
        tick += 1
        for pid, s in state.items():
            if not s["active"]:
                continue
            if len(s["seq"]) >= s["session_len"]:
                s["active"] = False
                continue

            resp = client.get(URL_NEXT, s["base"])
            payload = resp.json()

            # A served task is the serialized document itself (no "status" key);
            # terminal states come back as {"status": ...}.
            if "status" in payload:
                st = payload["status"]
                if st == "retry":
                    continue
                s["stop"] = st.upper()
                s["active"] = False
                continue

            if "id" not in payload:
                s["stop"] = f"unexpected:{str(payload)[:100]}"
                s["active"] = False
                continue

            doc = Document.objects.get(id=payload["id"])
            if doc.is_gold_unit:
                true_label = (doc.gold_solution or {}).get("classification")
            else:
                true_label = hidden_truth.get(doc.id)

            choice = answer_for(true_label, s["accuracy"], s["always"])
            result = {"classification": choice,
                      "span_highlight": make_spans(doc.text, s["profile"])}

            base_ms = {"expert": 42000, "good": 31000, "average": 24000,
                       "sloppy": 12000, "spammer": 3500}[s["profile"]]
            ms = max(1800, int(random.gauss(base_ms, base_ms * 0.25)))

            sub = client.post(URL_SUBMIT, {
                **s["base"], "document": str(doc.id), "result": result,
                "milliseconds_to_complete": ms,
            }, content_type="application/json")

            if sub.status_code != 201:
                s["stop"] = f"submit_error:{sub.status_code}"
                s["active"] = False
                continue

            ann = (Annotation.objects
                   .filter(document=doc, annotator__prolific_pid=pid)
                   .order_by('-created_at').first())
            if ann:
                s["ann_ids"].append(ann.id)
            s["seq"].append(("G" if doc.is_gold_unit else "R", choice, true_label))

    print(f"  Annotation phase finished after {tick} concurrent rounds.")

# --- Phase 3: backdate timestamps + collect per-worker results ---
for w_index, (pid, profile, accuracy, session_len, always) in enumerate(WORKERS):
    s = state[pid]
    for i, ann_id in enumerate(s["ann_ids"]):
        ts = s["start"] + datetime.timedelta(minutes=i * random.randint(3, 11))
        Annotation.objects.filter(id=ann_id).update(created_at=ts)

    enrollment = ProjectEnrollment.objects.get(project=project, annotator__prolific_pid=pid)
    gold_seq = [(c, t) for kind, c, t in s["seq"] if kind == "G"]
    gold_ok = sum(1 for c, t in gold_seq if c == t)
    reg_seq = [(c, t) for kind, c, t in s["seq"] if kind == "R"]
    reg_ok = sum(1 for c, t in reg_seq if c == t)

    report_rows.append({
        "pid": pid, "profile": profile, "accuracy": accuracy,
        "total": len(s["seq"]), "gold": len(gold_seq), "gold_ok": gold_ok,
        "regular": len(reg_seq), "regular_ok": reg_ok,
        "status": enrollment.status, "is_test": enrollment.annotator.is_test,
        "gold_done_field": enrollment.gold_tasks_completed,
        "gold_acc_field": enrollment.gold_accuracy,
        "stop": s["stop"],
    })
    print(f"  [{w_index+1:2}/10] {profile:<8} {pid[:12]}... "
          f"tasks={len(s['seq']):<3} reg={len(reg_seq):<3} gold={len(gold_seq)} "
          f"gold_ok={gold_ok} status={enrollment.status:<10} stop={s['stop']}")

# ------------------------------------------------------------ 7. RUN MACE
print("\nRunning MACE...")
from annotation.mace_service import run_mace_for_project
mace_out = run_mace_for_project(project.id)
ProjectLogEntry.objects.create(project=project, action="MACE Analysis",
                               details=str(mace_out.get("message", mace_out)))

# ------------------------------------------------------------- 8. REPORT
print("\n" + "=" * 78)
print("STUDY SIMULATION REPORT")
print("=" * 78)
print(f"Project : {project.name}  (slug={project.slug}, id={project.id})")
print(f"Status  : {project.status} | published={project.is_published}")
print(f"Config  : gold_freq={project.gold_injection_frequency} "
      f"min_gold_before_eval={project.min_gold_before_eval} "
      f"min_accuracy={project.min_accuracy_required} "
      f"min/max_per_doc={project.min_annotations_per_doc}/{project.max_annotations_per_doc}")

total_ann = Annotation.objects.filter(document__project=project).count()
real_ann = Annotation.objects.filter(document__project=project, is_test=False).count()
gold_ann = Annotation.objects.filter(document__project=project, document__is_gold_unit=True).count()
print(f"\nAnnotations: {total_ann} total | {real_ann} real (non-test) | {gold_ann} on gold units")

print("\n--- WORKERS ---")
print(f"{'PID':<26}{'profile':<9}{'tasks':>6}{'reg':>5}{'gold':>6}"
      f"{'gold_acc':>10}{'true_acc':>10}{'status':>11}{'MACE':>8}")
for r in report_rows:
    e = ProjectEnrollment.objects.get(project=project, annotator__prolific_pid=r["pid"])
    mace = f"{e.mace_competence_score:.3f}" if e.mace_competence_score is not None else "-"
    acc = f"{r['gold_acc_field']:.0%}" if r["gold_acc_field"] is not None else "-"
    true_acc = f"{r['regular_ok'] / r['regular']:.0%}" if r["regular"] else "-"
    print(f"{r['pid'][:24]:<26}{r['profile']:<9}{r['total']:>6}{r['regular']:>5}{r['gold']:>6}"
          f"{acc:>10}{true_acc:>10}{r['status']:>11}{mace:>8}")

print("\n--- DOCUMENT COVERAGE ---")
done = 0
for d in Document.objects.filter(project=project, is_gold_unit=False).order_by('external_id'):
    if d.current_annotations_count >= d.min_annotations_required:
        done += 1
print(f"Regular documents reaching the target of {project.min_annotations_per_doc} annotations: "
      f"{done}/{Document.objects.filter(project=project, is_gold_unit=False).count()}")

print("\n--- MACE vs INTENDED GROUND TRUTH (regular docs) ---")
agree = 0
total_pred = 0
for d in Document.objects.filter(project=project, is_gold_unit=False).order_by('external_id'):
    if d.mace_gold_label is None:
        continue
    total_pred += 1
    truth = hidden_truth[d.id]
    match = "OK " if d.mace_gold_label == truth else "DIFF"
    if d.mace_gold_label == truth:
        agree += 1
    print(f"{d.external_id}  intended={truth:<11} mace={d.mace_gold_label:<11} "
          f"conf={d.mace_confidence:.3f}  {match}")
print(f"\nMACE agreement with intended labels: {agree}/{total_pred}")
print(f"MACE run: {mace_out}")
print("\nDone.")
