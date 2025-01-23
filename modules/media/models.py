# media_manager/models.py
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models


def validate_file_size(value):
    """Validate file size (in bytes)."""
    max_size = 2 * 1024 * 1024  # 2 MB
    if value > max_size:
        raise ValidationError(
            f"File size must be below {max_size / (1024 * 1024)} MB.",
            params={'value': value}
        )

class Media(models.Model):
    collection_name = models.CharField(max_length=255) 
    file_name = models.CharField(max_length=255)
    file_path = models.TextField()
    mime_type = models.CharField(max_length=100)
    size = models.PositiveBigIntegerField(validators=[validate_file_size])
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    custom_properties = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    disk = models.CharField(max_length=191, null=True)

    def __str__(self):
        return self.file_name
    
    def upsert(
            collection_name: str,
            file_name: str,
            file_path: str,
            mime_type: str,
            file_size: int,
            disk: str,
            model_instance
    ) -> bool:
        try:
            # Validate the file size
            validate_file_size(file_size)
            
            # Get the ContentType for the model instance
            content_type = ContentType.objects.get_for_model(model_instance)

            # Perform the upsert operation
            return Media.objects.update_or_create(
                content_type=content_type,
                object_id=model_instance.id,
                defaults={
                    'collection_name': collection_name,
                    'file_name': file_name,
                    'file_path': file_path,
                    'mime_type': mime_type,
                    'disk': disk,
                    'size': file_size,
                }
            )

        except Exception as e:
            # Log the error if needed
            print(f"Error during upsert: {e}")
            # Return False on failure
            return False
