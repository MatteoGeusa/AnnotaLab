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

# This decorator says: "Execute this function AFTER (post) an Annotation has been saved"
@receiver(post_save, sender=Annotation)
def update_annotation_count_on_save(sender, instance, created, **kwargs):
    """
    If a new annotation is created, we update the parent document counter.
    """
    if created:
        doc = instance.document
        # We count how many annotations actually exist in the DB to be 100% sure
        real_count = doc.annotations.count()
        
        doc.current_annotations_count = real_count
        doc.save(update_fields=['current_annotations_count']) # We save only this field for speed

@receiver(post_delete, sender=Annotation)
def update_annotation_count_on_delete(sender, instance, **kwargs):
    """
    If we delete an annotation by mistake, the counter must decrease!
    """
    doc = instance.document
    doc.current_annotations_count = doc.annotations.count()
    doc.save(update_fields=['current_annotations_count'])