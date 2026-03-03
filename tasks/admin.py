# tasks/admin.py
from django.contrib import admin
from .models import Task, TaskUpdate, Notification

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'assigned_to', 'created_by', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'created_at', 'start_date')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'completed_at')

@admin.register(TaskUpdate)
class TaskUpdateAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'update_type', 'created_at')
    list_filter = ('update_type', 'created_at')
    search_fields = ('message',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('message',)