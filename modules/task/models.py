from django.db import models

# Create your models here.
class Task(models.Model):
    title = models.CharField(max_length=191)
    source = models.CharField(max_length=191)
    content = models.TextField()
    published = models.DateTimeField('date published')

    def __str__(self):
        return self.tutorial_title
