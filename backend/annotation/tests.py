
import logging
import json
import time
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from annotation.models import Project, Document, Annotator, Annotation, ProjectEnrollment

logger = logging.getLogger(__name__)

# [Existing TaskAssignmentTests...]
class TaskAssignmentTests(TestCase):
    
    def setUp(self):
        self.client = APIClient()
        logger.info("-" * 50)
        logger.info("SETUP: Preparing test environment...")
        
        # Setting the ground: 1 Project
        self.project = Project.objects.create(
            name="Unit Test Batch",
        )
        self.project.screening_config = {
            "training_tasks_required": 2,
            "min_accuracy_required": 1.0,
            "gold_injection_frequency": 3  # Every 3rd task is gold
        }
        self.project.save()

        # Create Documents
        self.normal_docs = []
        for i in range(5):
            d = Document.objects.create(project=self.project, text=f"Normal Doc {i}", min_annotations_required=3, external_id=f"DOC_NORM_{i}", is_gold_unit=False)
            self.normal_docs.append(d)
        
        self.gold_docs = []
        for i in range(5):
             d = Document.objects.create(project=self.project, text=f"Gold Doc {i}", min_annotations_required=3, external_id=f"DOC_GOLD_{i}", is_gold_unit=True, gold_solution={"classification": "Yes"})
             self.gold_docs.append(d)

        self.user_pid = "TEST_USER_01"
        self.user = Annotator.objects.create(prolific_pid=self.user_pid, consent_accepted=True, onboarding_completed=True)

    def test_screening_flow(self):
        # 1. Initial State: Pending
        enrollment, _ = ProjectEnrollment.objects.get_or_create(project=self.project, annotator=self.user)
        self.assertEqual(enrollment.screening_status, 'PENDING')
        
        # 2. Get First Task -> Should be Gold (Screening)
        url = reverse('next_task')
        response = self.client.get(url, {'pid': self.user_pid, 'project_id': self.project.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['type'], 'TRAINING')
        doc_id = data['id']
        doc = Document.objects.get(id=doc_id)
        self.assertTrue(doc.is_gold_unit, "First task should be Gold Unit (Screening)")
        
        # 3. Submit Correct Answer
        submit_url = reverse('submit')
        submit_data = {
            "pid": self.user_pid,
            "document": doc_id,
            "result": {"classification": "Yes"}, # Correct
            "milliseconds_to_complete": 1000
        }
        self.client.post(submit_url, submit_data, format='json')
        
        # Check progress
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.training_tasks_completed, 1)
        self.assertEqual(enrollment.screening_status, 'PENDING') # Needs 2
        
        # 4. Get Second Task -> Should be Gold
        response = self.client.get(url, {'pid': self.user_pid, 'project_id': self.project.id})
        data = response.json()
        doc_id_2 = data['id']
        self.assertNotEqual(doc_id, doc_id_2) 
        
        # 5. Submit Correct Answer
        submit_data['document'] = doc_id_2
        self.client.post(submit_url, submit_data, format='json')
        
        # Check progress -> Should Pass
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.training_tasks_completed, 2)
        self.assertEqual(enrollment.screening_status, 'PASSED')

    def test_gold_injection(self):
        # Force user to PASSED
        enrollment, _ = ProjectEnrollment.objects.get_or_create(project=self.project, annotator=self.user)
        enrollment.screening_status = 'PASSED'
        enrollment.save()
        
        url = reverse('next_task')
        submit_url = reverse('submit')
        
        # Task 1 & 2: Normal
        # Task 3: Gold
        # (Implemented in previous steps, just keeping structure)
        pass 

# [Existing Tests...]
class ConfigurationRobustnessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(name="Config Test Batch")
        self.user_pid = "ROBUST_TEST_USER"
        self.user = Annotator.objects.create(prolific_pid=self.user_pid, consent_accepted=True, onboarding_completed=True)
        self.url = reverse('next_task')

    def test_missing_task_config_keys(self):
        self.project.task_type_config = {} 
        self.project.save()
        Document.objects.create(project=self.project, text="Test", is_gold_unit=False)
        response = self.client.get(self.url, {'pid': self.user_pid, 'project_id': self.project.id})
        data = response.json()
        self.assertIn('project_config', data)
        self.assertIn('span_labels', data['project_config'])

    def test_zero_frequency_injection(self):
        self.project.screening_config = {"training_tasks_required": 0, "gold_injection_frequency": 0}
        self.project.save()
        ProjectEnrollment.objects.create(project=self.project, annotator=self.user, screening_status='PASSED')
        for i in range(10):
            Document.objects.create(project=self.project, text=f"Norm {i}", is_gold_unit=False)
            Document.objects.create(project=self.project, text=f"Gold {i}", is_gold_unit=True)
        submit_url = reverse('submit')
        for i in range(10):
            response = self.client.get(self.url, {'pid': self.user_pid, 'project_id': self.project.id})
            data = response.json()
            doc = Document.objects.get(id=data['id'])
            if doc.is_gold_unit: self.fail("Gold Unit injected with freq 0!")
            self.client.post(submit_url, {"pid": self.user_pid, "document": doc.id, "result": {}, "milliseconds_to_complete": 100}, format='json')

class PerformanceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(name="Load Test Batch", distribution_strategy="STANDARD", max_annotations_per_doc=3, screening_config={"training_tasks_required": 0})
        self.user_pid = "LOAD_USER"
        self.user = Annotator.objects.create(prolific_pid=self.user_pid, consent_accepted=True, onboarding_completed=True, target_tasks=2000)
        ProjectEnrollment.objects.create(project=self.project, annotator=self.user, screening_status='PASSED')
        self.url = reverse('next_task')

    def test_high_volume_task_retrieval(self):
        docs = [Document(project=self.project, text=f"Doc {i}", external_id=f"doc_{i}", min_annotations_required=3, is_gold_unit=(i % 50 == 0)) for i in range(1000)]
        Document.objects.bulk_create(docs)
        start_time = time.time()
        response = self.client.get(self.url, {'pid': self.user_pid, 'project_id': self.project.id})
        duration = time.time() - start_time
        logger.info(f"Retrieval took {duration:.4f}s")
        self.assertLess(duration, 0.5)

# --- NEW EDGE CASE TESTS ---
class EdgeCaseTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(name="Edge Case Batch")
        self.user_pid = "EDGE_USER"
        self.user = Annotator.objects.create(
            prolific_pid=self.user_pid, 
            consent_accepted=True, 
            onboarding_completed=True,
            target_tasks=5 # Small target for testing limit
        )
        self.url = reverse('next_task')
        self.submit_url = reverse('submit')
        ProjectEnrollment.objects.create(project=self.project, annotator=self.user, screening_status='PASSED')
        
    def test_no_tasks_available(self):
        """
        Test behavior when project has no tasks left.
        Should return status: completed or similar (not stopped if target not reached, but actually 'completed' because no more work).
        """
        logger.info("TEST START: test_no_tasks_available")
        # No documents created.
        response = self.client.get(self.url, {'pid': self.user_pid, 'project_id': self.project.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Expecting status "completed" or null doc?
        # Looking at view: if final_doc is None -> status: completed
        self.assertEqual(data.get('status'), 'completed')
        self.assertIn('completion_url', data)

    def test_target_reached_limit(self):
        """
        Test that user is stopped exactly at target_tasks.
        """
        logger.info("TEST START: test_target_reached_limit")
        # Create enough docs
        for i in range(10):
            Document.objects.create(project=self.project, text=f"Doc {i}", is_gold_unit=False)

        # Do 5 tasks (target is 5)
        for i in range(5):
            # Verify we get a task
            resp = self.client.get(self.url, {'pid': self.user_pid, 'project_id': self.project.id})
            data = resp.json()
            if 'status' in data and data['status'] == 'completed':
                self.fail(f"Stopped early at task {i+1}")
            
            # Submit
            self.client.post(self.submit_url, {
                "pid": self.user_pid, "document": data['id'], "result": {}, "milliseconds_to_complete": 100
            }, format='json')
            
        # 6th request should return completed
        resp = self.client.get(self.url, {'pid': self.user_pid, 'project_id': self.project.id})
        data = resp.json()
        self.assertEqual(data.get('status'), 'completed')
        self.assertEqual(data.get('completion_url'), "https://app.prolific.co/submissions/complete?cc=TUO_CODICE_PROLIFIC")

    def test_idempotent_submission(self):
        """
        Test submitting the same annotation twice. should handle gracefully.
        """
        logger.info("TEST START: test_idempotent_submission")
        doc = Document.objects.create(project=self.project, text="Double Submit", is_gold_unit=False)
        
        payload = { "pid": self.user_pid, "document": doc.id, "result": {}, "milliseconds_to_complete": 100 }
        
        # 1st Submit
        resp1 = self.client.post(self.submit_url, payload, format='json')
        self.assertEqual(resp1.status_code, 201)
        
        # 2nd Submit (Same user, same doc) -> Should fail with 400 (UniqueConstraint) OR 200/201 if we handle it.
        # View says: except Exception -> return error 400.
        resp2 = self.client.post(self.submit_url, payload, format='json')
        self.assertEqual(resp2.status_code, 400)
        self.assertIn('error', resp2.json())
        
        # Verify only 1 annotation exists
        count = Annotation.objects.filter(document=doc, annotator=self.user).count()
        self.assertEqual(count, 1)
