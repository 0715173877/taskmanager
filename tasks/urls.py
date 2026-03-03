# tasks/urls.py
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Task CRUD operations
    path('create/', views.create_task, name='create_task'),
    path('<int:task_id>/', views.task_detail, name='task_detail'),
    path('<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('<int:task_id>/delete/', views.delete_task, name='delete_task'),
    
    # Task updates and actions
    path('<int:task_id>/add-update/', views.add_task_update, name='add_task_update'),
    path('<int:task_id>/update-status/', views.update_task_status, name='update_task_status'),
    
    # Extension management
    path('<int:task_id>/request-extension/', views.request_extension, name='request_extension'),
    path('<int:task_id>/manage-extension/', views.manage_extension, name='manage_extension'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/mark-read/', 
         views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', 
         views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # API endpoints for HTMX
    path('api/task-list/', views.task_list_api, name='task_list_api'),
    
    # Filtering
    path('filter/', views.filter_tasks, name='filter_tasks'),
    
    # Reports (only basic one for now)
    path('reports/', views.reports, name='reports'),
]