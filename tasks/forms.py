# tasks/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Task, TaskUpdate

class TaskForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = Task
        fields = ['name', 'description', 'assigned_to', 'start_date', 'end_date', 'estimated_days']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.groups.filter(name='Manager').exists():
            self.fields['assigned_to'].queryset = User.objects.filter(groups__name='Staff')
        else:
            self.fields['assigned_to'].queryset = User.objects.filter(id=user.id)
            self.fields['assigned_to'].initial = user
            self.fields['assigned_to'].widget = forms.HiddenInput()

class TaskUpdateForm(forms.ModelForm):
    class Meta:
        model = TaskUpdate
        fields = ['update_type', 'message', 'file']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }

class ExtensionRequestForm(forms.Form):
    extension_days = forms.IntegerField(min_value=1, max_value=30)
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))

class TaskStatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['status']