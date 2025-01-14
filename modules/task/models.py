from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=191)
    source = models.CharField(max_length=191)
    content = models.TextField()
    published = models.DateTimeField('date published')

    def __str__(self):
        return self.title


class Locking(models.Model):
    task_id = models.BigIntegerField(primary_key=True)
    is_locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="locked_task")
    locked_at = models.DateTimeField(null=True, blank=True)

    
    @staticmethod
    def lock_task(user, task):
        Locking.objects.update_or_create(
            task_id=task.id,
            defaults={
                "is_locked": True,
                "locked_by": user,
                "locked_at": now(),
            }
        )
