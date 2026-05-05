from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Annotation


'''
The system implements a self-healing mechanism for data validation. 
When a researcher manually deletes a rejected annotation (e.g., from a spammer), 
the post_delete signal triggers an automatic update of the document's completion status. 
By decrementing the annotation count, the system recognizes the document as 'incomplete' 
and places it back into the assignment pool, guaranteeing that every document eventually 
receives the target number of valid annotations.
'''

#Execute this function AFTER (post) an Annotation has been saved
@receiver(post_save, sender=Annotation)
def update_annotation_count_on_save(sender, instance, created, **kwargs):
    """
    Triggered when an Annotation is saved.
    Increments the 'current_annotations_count' on the parent Document.
    """
    if created:
        doc = instance.document
        # We count the actual records in the DB to ensure consistency
        # (Safer than blindly incrementing +1)
        doc.current_annotations_count = doc.annotations.filter(is_test=False).count()
        # We only update the specific field to optimize performance
        doc.save(update_fields=['current_annotations_count'])

@receiver(post_delete, sender=Annotation)
def update_annotation_count_on_delete(sender, instance, **kwargs):
    """
    Triggered when an Annotation is deleted (e.g., removing spam).
    Decrements the 'current_annotations_count'.
    
    This effectively 're-opens' the task if the count drops below 
    the 'min_annotations_required' threshold.
    """
    doc = instance.document
    doc.current_annotations_count = doc.annotations.filter(is_test=False).count()
    doc.save(update_fields=['current_annotations_count'])