from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    file = forms.FileField(required=True)  # Add a file field for file upload

    class Meta:
        model = Task
        fields = ['title', 'source', 'content', 'published', 'file']
        widgets = {
            'published': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
