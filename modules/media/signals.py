from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import Media

@receiver(post_delete)
def cascade_delete_related_media(sender, instance, **kwargs):
    """
    Cascade delete related Media objects when a referenced object is deleted.
    """
    # Get the ContentType for the deleted object
    content_type = ContentType.objects.get_for_model(sender)

    # Delete all Media objects related to the deleted object
    Media.objects.filter(content_type=content_type, object_id=instance.id).delete()
