# tasks/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('needs_extension', 'Needs Extension'),
        ('extension_granted', 'Extension Granted'),
        ('closed', 'Closed'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField()
    estimated_days = models.PositiveIntegerField(help_text="Estimated number of work days")
    extension_days = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("can_view_all_tasks", "Can view all tasks"),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def is_overdue(self):
        return self.end_date < timezone.now().date() and not self.is_completed
    
    @property
    def total_days(self):
        return self.estimated_days + self.extension_days

class TaskUpdate(models.Model):
    UPDATE_TYPES = [
        ('progress', 'Progress Update'),
        ('completion', 'Completion Request'),
        ('extension', 'Extension Request'),
        ('approval', 'Manager Approval'),
        ('comment', 'Comment'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='updates')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='task_updates/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.update_type} for {self.task.name}"

# tasks/models.py - Update Notification model
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_updated', 'Task Updated'),
        ('extension_requested', 'Extension Requested'),
        ('task_completed', 'Task Completed'),
        ('task_approved', 'Task Approved'),
        ('task_overdue', 'Task Overdue'),
        ('task_comment', 'Task Comment'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} - {self.user.username}"
    
    @property
    def get_icon(self):
        """Get Bootstrap icon based on notification type"""
        icons = {
            'task_assigned': 'bi-plus-circle',
            'task_updated': 'bi-pencil',
            'extension_requested': 'bi-clock-history',
            'task_completed': 'bi-check-circle',
            'task_approved': 'bi-check-lg',
            'task_overdue': 'bi-exclamation-triangle',
            'task_comment': 'bi-chat',
        }
        return icons.get(self.notification_type, 'bi-bell')