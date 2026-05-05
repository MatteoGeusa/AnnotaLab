import logging
import os
import tempfile
import csv
import numpy as np
from collections import defaultdict
from django.core.exceptions import ObjectDoesNotExist
from .models import Project, Annotation, ProjectEnrollment, Document

logger = logging.getLogger(__name__)

def run_mace_for_project(project_id):
    """
    Extracts annotations for a project, runs the MACE algorithm,
    and updates the models with the computed metrics.
    
    If the official MACE python package is installed, it uses it.
    Otherwise, it shows how the data should be structured and provides a mock/fallback logic.
    """
    project = Project.objects.get(id=project_id)
    
    # 1. Fetch Annotations
    # Exclude gold units, we only use unsupervised MACE on standard instances.
    annotations = Annotation.objects.filter(
        document__project=project,
        document__is_gold_unit=False,
        is_test=False
    ).select_related('document', 'annotator')
    
    if not annotations.exists():
        return {"status": "error", "message": "No annotations found to run MACE."}

    # 2. Build the Data Matrix (Documents x Annotators)
    # Rows = Document IDs, Columns = Annotator Prolific PIDs
    # Value = The classification label
    
    doc_ids = set()
    annotator_pids = set()
    data_dict = defaultdict(dict) # {doc_id: {annotator_pid: label}}
    
    for ann in annotations:
        doc_id = str(ann.document.id)
        annotator_pid = ann.annotator.prolific_pid
        label = ann.result.get('classification')
        
        # Only process if there is a classification label
        if label:
            doc_ids.add(doc_id)
            annotator_pids.add(annotator_pid)
            data_dict[doc_id][annotator_pid] = label

    from_doc_ids = sorted(list(doc_ids))
    from_annotators = sorted(list(annotator_pids))
    
    if len(from_annotators) < 2:
        return {"status": "error", "message": "Need at least 2 distinct annotators to estimate competence."}

    # 3. Use actual MACE python package
    mace_results = None
    try:
        from .mace import MACE
        
        # Write to a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
            temp_file_name = f.name
            writer = csv.writer(f)
            for doc_id in from_doc_ids:
                row = []
                for pid in from_annotators:
                    row.append(data_dict[doc_id].get(pid, ""))
                writer.writerow(row)
        
        try:
            mace_model = MACE(temp_file_name, continuous=False)
            mace_model.initialize(init_noise=0.5)
            # Run Variational Bayes EM
            mace_model.run(num_iters=50, smoothing=0.01, num_restarts=10, alpha=0.5, beta=0.5, use_em=False, controls_file=None)
            
            # Extract results
            predictions_list = mace_model.decode(threshold=1.0)
            entropies_list = mace_model.get_label_entropies()
            
            competence = {}
            spam_bias = {}
            predictions = {}
            confidence = {}
            
            spamming = mace_model.spamming
            thetas = mace_model.thetas
            
            if spamming is None or thetas is None:
                raise ValueError("MACE training failed to update internal probability distributions.")
            
            # MACE indexes annotators based on column order (from_annotators)
            for j, pid in enumerate(from_annotators):
                comp_score = float(spamming[j, 1])  # probability of knowing
                guess_prob = float(spamming[j, 0])  # probability of guessing
                
                # Format the spamming strategy distribution
                bias_dict = {}
                for k, label_name in enumerate(mace_model.int2string):
                    bias_dict[label_name] = float(thetas[j, k])
                    
                competence[pid] = comp_score
                spam_bias[pid] = {
                    "guess_probability": guess_prob,
                    "strategy": bias_dict
                }
                
            # MACE indexes documents based on row order (from_doc_ids)
            for i, doc_id in enumerate(from_doc_ids):
                pred = predictions_list[i]
                ent = float(entropies_list[i]) if entropies_list[i] != float('-inf') else 0.0
                
                # Convert entropy to a simple 0-1 confidence score (lower entropy = higher confidence)
                # Max entropy for N labels is ln(N)
                max_entropy = np.log(mace_model.num_labels) if mace_model.num_labels > 1 else 1.0
                conf_score = max(0.0, 1.0 - (ent / max_entropy)) if max_entropy > 0 else 1.0
                
                predictions[doc_id] = pred
                confidence[doc_id] = conf_score
                
            mace_results = {
                "competence": competence,
                "spam_bias": spam_bias,
                "predictions": predictions,
                "confidence": confidence
            }
            
        finally:
            if os.path.exists(temp_file_name):
                os.remove(temp_file_name)
        
    except Exception as e:
        logger.error(f"Error running MACE: {e}", exc_info=True)
        return {"status": "error", "message": f"MACE execution failed: {str(e)}"}

    # 4. Save Results to Database
    # Update Enrollments
    updated_enrollments = 0
    for pid, score in mace_results.get("competence", {}).items():
        try:
            enrollment = ProjectEnrollment.objects.get(
                project=project,
                annotator__prolific_pid=pid
            )
            enrollment.mace_competence_score = score
            enrollment.mace_spam_bias = mace_results.get("spam_bias", {}).get(pid, {})
            enrollment.save(update_fields=["mace_competence_score", "mace_spam_bias"])
            updated_enrollments += 1
        except ObjectDoesNotExist:
            continue
            
    # Update Documents
    updated_docs = 0
    for doc_id, label in mace_results.get("predictions", {}).items():
        try:
            doc = Document.objects.get(id=doc_id)
            doc.mace_gold_label = label
            doc.mace_confidence = mace_results.get("confidence", {}).get(doc_id, 0.0)
            doc.save(update_fields=["mace_gold_label", "mace_confidence"])
            updated_docs += 1
        except ObjectDoesNotExist:
            continue
            
    return {
        "status": "success", 
        "message": f"MACE estimation complete. Updated {updated_enrollments} annotators and {updated_docs} documents."
    }
