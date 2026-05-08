import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Project, Annotator, ProjectEnrollment, Document, Annotation

class AnnotaLabAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.project = Project.objects.create(
            name="Test Project",
            slug="test-project",
            status="LIVE",
            is_published=True,
            enable_screening=True,
            screening_config=[{"id": "q1", "required": True, "label": "Age?"}],
            enable_codebook=True,
            codebook_content="Codebook info",
            enable_instructions=True,
            instructions_content="Instructions info",
            informed_consent_config="Consent info",
            min_accuracy_required=0.5,
            min_gold_before_eval=1,
            enable_gold_units=True,
            gold_injection_frequency=2
        )
        self.doc1 = Document.objects.create(project=self.project, text="Doc 1", is_gold_unit=False)
        self.doc2 = Document.objects.create(project=self.project, text="Doc 2", is_gold_unit=True, gold_solution={"classification": "A"})
        self.pid = "test_pid_123"

    def test_full_annotator_flow(self):
        # 1. Initialize Session
        resp = self.client.post(reverse('session'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200, "Session should initialize")
        self.assertEqual(resp.json()['step'], 'CONSENT', "First step should be CONSENT")
        
        # 2. Get Consent & Accept Consent
        resp = self.client.get(reverse('get_consent'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200, "Should return consent text")
        
        resp = self.client.post(reverse('consent'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['next_step'], 'SCREENING')

        # 3. Get Screening & Submit Screening
        resp = self.client.get(reverse('get_screening'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)
        
        # Try invalid screening (missing required)
        resp = self.client.post(reverse('screening'), {'prolific_pid': self.pid, 'project_slug': self.project.slug, 'responses': {}}, content_type="application/json")
        self.assertEqual(resp.status_code, 400, "Should reject empty screening responses if required")
        
        # Valid screening
        resp = self.client.post(reverse('screening'), {'prolific_pid': self.pid, 'project_slug': self.project.slug, 'responses': {"q1": "25"}}, content_type="application/json")
        self.assertEqual(resp.status_code, 200, "Should accept valid screening")

        # 4. Get Codebook & Complete Codebook
        resp = self.client.get(reverse('get_codebook'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.post(reverse('codebook'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)

        # 5. Get Instructions & Complete Onboarding
        resp = self.client.get(reverse('get_instructions'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.post(reverse('onboarding'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)

        # 6. Get Next Task
        resp = self.client.get(reverse('next_task'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)
        doc_id = resp.json().get('id')
        self.assertIsNotNone(doc_id, "Should return a document ID")

        # 7. Submit Annotation
        resp = self.client.post(reverse('submit'), {
            'prolific_pid': self.pid, 
            'project_slug': self.project.slug,
            'document': doc_id,
            'result': {"classification": "A"},
            'milliseconds_to_complete': 1000
        }, content_type="application/json")
        self.assertEqual(resp.status_code, 201, f"Failed to submit annotation: {resp.content}")

    def test_edge_cases(self):
        # Missing PID
        resp = self.client.post(reverse('session'), {'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 400)

        # Inactive project
        self.project.status = 'DRAFT'
        self.project.save()
        resp = self.client.post(reverse('session'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 404)

        self.project.status = 'LIVE'
        self.project.save()

        # Test double consent
        self.client.post(reverse('consent'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        resp = self.client.get(reverse('get_consent'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 400, "Should prevent getting consent again if already consented")

    def test_admin_access(self):
        self.client.login(username='admin', password='password')
        resp = self.client.get('/admin/annotation/project/')
        self.assertEqual(resp.status_code, 200)
        
        # Test custom admin views like enrollment list view
        resp = self.client.get(f'/admin/annotation/projectenrollment/?project__id__exact={self.project.id}')
        self.assertEqual(resp.status_code, 200)
        
        # If accessing without project filter, should redirect
        resp = self.client.get('/admin/annotation/projectenrollment/')
        self.assertEqual(resp.status_code, 302, "Should redirect when no project filter is active")

    def test_gold_unit_evaluation(self):
        # Onboard a user and make them submit a wrong gold unit to trigger exclusion
        self.client.post(reverse('consent'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.client.post(reverse('screening'), {'prolific_pid': self.pid, 'project_slug': self.project.slug, 'responses': {"q1": "25"}}, content_type="application/json")
        self.client.post(reverse('codebook'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.client.post(reverse('onboarding'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})

        # Submit to gold doc (doc2) with wrong answer
        # we need to make sure the user isn't marked as test, so is_test should be False
        # Project is PUBLISHED so is_test should be False by default for new session unless is_test=true passed
        
        resp = self.client.post(reverse('submit'), {
            'prolific_pid': self.pid, 
            'project_slug': self.project.slug,
            'document': self.doc2.id,
            'result': {"classification": "WRONG_ANSWER"},
            'milliseconds_to_complete': 1000
        }, content_type="application/json")
        self.assertEqual(resp.status_code, 201)

        enrollment = ProjectEnrollment.objects.get(project=self.project, annotator__prolific_pid=self.pid)
        print(f"DEBUG: status={enrollment.status}, is_test={enrollment.annotator.is_test}, gold_tasks={enrollment.gold_tasks_completed}, gold_acc={enrollment.gold_accuracy}")
        self.assertEqual(enrollment.status, 'EXCLUDED', "Annotator should be EXCLUDED due to gold unit failure")

    def test_completed_flow(self):
        # We need documents to test exhaustion
        # To exhaust, user needs to complete `documents_per_annotator` docs (which is 2)
        self.client.post(reverse('consent'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.client.post(reverse('screening'), {'prolific_pid': self.pid, 'project_slug': self.project.slug, 'responses': {"q1": "25"}}, content_type="application/json")
        self.client.post(reverse('codebook'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.client.post(reverse('onboarding'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        
        # Task 1
        resp = self.client.get(reverse('next_task'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)
        doc1_id = resp.json()['id']
        
        self.client.post(reverse('submit'), {
            'prolific_pid': self.pid, 
            'project_slug': self.project.slug,
            'document': doc1_id,
            'result': {"classification": "A"},
            'milliseconds_to_complete': 1000
        }, content_type="application/json")
        
        # Task 2
        resp = self.client.get(reverse('next_task'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)
        doc2_id = resp.json()['id']
        
        self.client.post(reverse('submit'), {
            'prolific_pid': self.pid, 
            'project_slug': self.project.slug,
            'document': doc2_id,
            'result': {"classification": "A"},
            'milliseconds_to_complete': 1000
        }, content_type="application/json")
        
        # Now if we ask for next task, it should be completed
        resp = self.client.get(reverse('next_task'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'completed', "Should return completed status after doing required docs")

    def test_distribution_strategies(self):
        # Change strategy to FULL_OVERLAP
        self.project.distribution_strategy = 'FULL_OVERLAP'
        self.project.save()
        
        self.client.post(reverse('consent'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.client.post(reverse('screening'), {'prolific_pid': self.pid, 'project_slug': self.project.slug, 'responses': {"q1": "25"}}, content_type="application/json")
        self.client.post(reverse('codebook'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.client.post(reverse('onboarding'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        
        # Get next task should work normally
        resp = self.client.get(reverse('next_task'), {'prolific_pid': self.pid, 'project_slug': self.project.slug})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('id' in resp.json())

