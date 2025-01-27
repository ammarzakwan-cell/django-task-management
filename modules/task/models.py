from django.db import models
from django.contrib.auth.models import User
from auditlog.registry import auditlog

# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=191)
    source = models.CharField(max_length=191)
    content = models.TextField()
    published = models.DateTimeField('date published')
    locked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="locked_task")
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    
    
    def lock_task(self, user):
        self.locked_by = user
        self.is_locked = True
        self.save()

    def unlock_task(self):
        self.locked_by = None
        self.is_locked = False
        self.save()

auditlog.register(Task, exclude_fields=['locked_by', 'is_locked'])