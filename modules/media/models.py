# media_manager/models.py
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Media(models.Model):
    collection_name = models.CharField(max_length=255)  # Group files logically
    file_name = models.CharField(max_length=255)  # File name
    file_path = models.TextField()  # Path to the file on S3
    mime_type = models.CharField(max_length=100)  # MIME type of the file
    size = models.PositiveBigIntegerField()  # File size in bytes
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # Polymorphic link
    object_id = models.PositiveIntegerField()  # Polymorphic link ID
    content_object = GenericForeignKey('content_type', 'object_id')  # Actual linked object
    custom_properties = models.JSONField(default=dict, blank=True)  # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name
    
    def upsert(
            collection_name: str,
            file_name: str,
            file_path: str,
            mime_type: str,
            file_size: int,
            model_instance
    ):
        # Get the content type of the model instance
        content_type = ContentType.objects.get_for_model(model_instance)

        # Look for an existing media entry
        Media.objects.update_or_create(
            content_type=content_type,
            object_id=model_instance.id,
            defaults={
                'collection_name': collection_name,
                'file_name': file_name,
                'file_path': file_path,
                'mime_type': mime_type,
                'size': file_size,
            }
        )
