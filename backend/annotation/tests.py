import logging
from django.test import TestCase
from annotation.models import Project, Document, Annotator, Annotation 

# Configure logger to print to console
logger = logging.getLogger(__name__)

class TaskAssignmentTests(TestCase):
    
    def setUp(self):
        logger.info("-" * 50)
        logger.info("SETUP: Preparing test environment...")
        
        # Setting the ground: 1 Project, 1 Document, 1 User
        self.project = Project.objects.create(name="Unit Test Batch")
        logger.info(f"SETUP: Created Project '{self.project.name}' (ID: {self.project.id})")
        
        self.doc = Document.objects.create(
            project=self.project, 
            text="Test content", 
            min_annotations_required=3,
            external_id="DOC_TEST_01"
        )
        logger.info(f"SETUP: Created Document ID {self.doc.id} (Min Annotations: {self.doc.min_annotations_required})")
        
        self.user = Annotator.objects.create(prolific_pid="TEST_USER")
        logger.info(f"SETUP: Created Annotator '{self.user.prolific_pid}'")
        logger.info("-" * 50)

    def test_user_cannot_annotate_same_doc_twice(self):
        """
        Test that if the user has already done the task, the system knows.
        """
        logger.info("TEST START: test_user_cannot_annotate_same_doc_twice")
        
        # 1. User performs the first annotation
        logger.info(f"STEP 1: User {self.user.prolific_pid} annotates Doc {self.doc.id}...")
        Annotation.objects.create(document=self.doc, annotator=self.user, result={})
        logger.info("STEP 1: Annotation saved in DB.")
        
        # 2. Ask DB: "Give me documents NOT done by this user"
        logger.info(f"STEP 2: Executing 'exclude' query for user {self.user.prolific_pid}...")
        
        available_docs = Document.objects.exclude(
            annotations__annotator=self.user
        )
        
        count = available_docs.count()
        logger.info(f"STEP 3: Query result -> Found {count} available documents.")

        # 3. Assert: The list must be empty
        if count == 0:
            logger.info("ASSERT: SUCCESS. No available documents found (Correct).")
        else:
            logger.error(f"ASSERT: FAILED. Found {count} documents but expected 0!")

        self.assertEqual(count, 0)
        logger.info("TEST END: test_user_cannot_annotate_same_doc_twice COMPLETED.\n")

    def test_redundancy_limit(self):
        """
        Test that after 3 annotations the document is considered 'finished'.
        """
        logger.info("TEST START: test_redundancy_limit")
        
        u1 = Annotator.objects.create(prolific_pid="U1")
        u2 = Annotator.objects.create(prolific_pid="U2")
        u3 = Annotator.objects.create(prolific_pid="U3")
        logger.info("STEP 1: Created 3 new annotators (U1, U2, U3)")

        # Three users annotate the same doc
        logger.info(f"STEP 2: All 3 annotate Document {self.doc.id}...")
        Annotation.objects.create(document=self.doc, annotator=u1, result={})
        Annotation.objects.create(document=self.doc, annotator=u2, result={})
        Annotation.objects.create(document=self.doc, annotator=u3, result={})
        logger.info("STEP 2: 3 Annotations saved.")
        
        # Update counter (Manual Simulation)
        logger.info("STEP 3: [SIMULATION] Manually updating current_annotations_count to 3")
        logger.info("(Note: In production this step should be automatic via Signals)")
        self.doc.current_annotations_count = 3
        self.doc.save()

        # Looking for documents still to do (count < 3)
        logger.info("STEP 4: Query documents with current_annotations_count < 3...")
        todos = Document.objects.filter(current_annotations_count__lt=3)
        
        count = todos.count()
        logger.info(f"STEP 5: Found {count} incomplete documents.")
        
        if count == 0:
            logger.info("ASSERT: SUCCESS. The document is considered complete.")
        
        self.assertEqual(count, 0)
        logger.info("TEST END: test_redundancy_limit COMPLETED.\n")