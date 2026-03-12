import os
import sys
import django
from dotenv import load_dotenv

# Setup Django environment
load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from annotation.models import Project, Annotator, Document, Annotation, ProjectEnrollment
from annotation.mace_service import run_mace_for_project

def run():
    print("=== SETUP MACE TEST ===")
    
    # 1. Clean up old test data if exists
    Project.objects.filter(name="MACE Test Project").delete()
    Annotator.objects.filter(prolific_pid__in=["EXPERT_A", "AVERAGE_B", "SPAMMER_C"]).delete()

    # 2. Create a dummy project
    project = Project.objects.create(name="MACE Test Project", description="Testing MACE")
    
    # 3. Create 15 documents
    docs = []
    # Arbitrary ground truth (hidden from MACE naturally)
    true_labels = [
        "Yes", "No", "Yes", "Yes", "No", 
        "Ambiguous", "Yes", "No", "Ambiguous", "Yes",
        "No", "No", "Yes", "Ambiguous", "No"
    ]
    
    for i in range(15):
        doc = Document.objects.create(project=project, text=f"Document {i}", external_id=f"doc_{i}")
        docs.append(doc)
        
    # 4. Create annotators
    # A is an EXPERT (always agrees with truth)
    # B is AVERAGE (makes some mistakes, maybe 70% accuracy)
    # C is a SPAMMER (always answers "Yes" regardless of the text)
    annotator_a = Annotator.objects.create(prolific_pid="EXPERT_A")
    annotator_b = Annotator.objects.create(prolific_pid="AVERAGE_B")
    annotator_c = Annotator.objects.create(prolific_pid="SPAMMER_C")
    
    ProjectEnrollment.objects.create(project=project, annotator=annotator_a)
    ProjectEnrollment.objects.create(project=project, annotator=annotator_b)
    ProjectEnrollment.objects.create(project=project, annotator=annotator_c)
    
    # 5. Create annotations
    for i, doc in enumerate(docs):
        truth = true_labels[i]
        
        # Expert A is basically 100% correct
        a_label = truth
        Annotation.objects.create(document=doc, annotator=annotator_a, result={"classification": a_label})
        
        # Average B makes some mistakes
        b_label = truth if i % 3 != 0 else "Yes" 
        Annotation.objects.create(document=doc, annotator=annotator_b, result={"classification": b_label})
        
        # Spammer C always says "Yes" 
        Annotation.objects.create(document=doc, annotator=annotator_c, result={"classification": "Yes"})
        
    # 6. Run MACE
    print(f"\nCreated {len(docs)} documents and 3 annotators.")
    print("Running MACE algorithm...")
    result = run_mace_for_project(project.id)
    print("Result:", result)
    
    # 7. Check results
    print("\n=== MACE EVALUATION RESULTS ===")
    print("\n--- Annotator Competence ---")
    for pid in ["EXPERT_A", "AVERAGE_B", "SPAMMER_C"]:
        enrollment = ProjectEnrollment.objects.get(project=project, annotator__prolific_pid=pid)
        score = enrollment.mace_competence_score or 0.0
        bias = enrollment.mace_spam_bias.get("strategy", {})
        print(f"Annotator {pid:10}: Competence = {score:.3f}")
        # Show what they do when they guess
        if "Yes" in bias:
            print(f"  -> When guessing, probability of saying 'Yes': {bias['Yes']:.2f}")

    print("\n--- Document Predictions ---")
    correct_predictions = 0
    for i, doc in enumerate(docs):
        doc.refresh_from_db()
        mace_pred = doc.mace_gold_label
        truth = true_labels[i]
        conf = doc.mace_confidence or 0.0
        is_correct = mace_pred == truth
        if is_correct:
            correct_predictions += 1
            
        mark = "✅" if is_correct else "❌"
        print(f"Doc {i:2} [Truth: {truth:9}] | MACE: {mace_pred:9} (Conf: {conf:.2f}) {mark}")
        
    print(f"\nFinal Accuracy of MACE relative to Ground Truth: {correct_predictions}/{len(docs)} ({(correct_predictions/len(docs))*100:.1f}%)")
    print("Notice how MACE filters out the Spammer C (who gets low competence) and mostly trusts A and B!")

if __name__ == '__main__':
    run()
