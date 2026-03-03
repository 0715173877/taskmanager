# tasks/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.utils import timezone
from .models import Task, TaskUpdate, Notification
from .forms import TaskForm, TaskUpdateForm, ExtensionRequestForm, TaskStatusForm
import json

@login_required
def dashboard(request):
    user = request.user
    is_manager = user.groups.filter(name='Manager').exists()
    
    if is_manager:
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(assigned_to=user)
    
    # Calculate statistics
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status='pending').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    completed_tasks = tasks.filter(status='completed').count()
    needs_extension_tasks = tasks.filter(status='needs_extension').count()
    
    context = {
        'tasks': tasks,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'needs_extension_tasks': needs_extension_tasks,
        'is_manager': is_manager,
    }
    return render(request, 'tasks/dashboard.html', context)

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            
            # Create initial update
            TaskUpdate.objects.create(
                task=task,
                user=request.user,
                update_type='progress',
                message=f'Task created by {request.user.get_full_name() or request.user.username}'
            )
            
            # Create notification for assigned user
            if task.assigned_to != request.user:
                Notification.objects.create(
                    user=task.assigned_to,
                    notification_type='task_assigned',
                    message=f'You have been assigned a new task: {task.name}',
                    task=task
                )
            
            messages.success(request, 'Task created successfully!')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskForm(user=request.user)
    
    return render(request, 'tasks/create_task.html', {'form': form})

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user has permission to view this task
    if not (request.user == task.assigned_to or request.user == task.created_by or 
            request.user.groups.filter(name='Manager').exists()):
        messages.error(request, 'You do not have permission to view this task.')
        return redirect('tasks:dashboard')
    
    updates = task.updates.all().order_by('-created_at')
    
    if request.method == 'POST':
        if 'add_update' in request.POST:
            update_form = TaskUpdateForm(request.POST, request.FILES)
            if update_form.is_valid():
                update = update_form.save(commit=False)
                update.task = task
                update.user = request.user
                update.save()
                
                if update.update_type == 'completion':
                    task.status = 'completed'
                    task.is_completed = True
                    task.completed_at = timezone.now()
                    task.save()
                    
                    # Notify manager
                    Notification.objects.create(
                        user=task.created_by,
                        notification_type='task_completed',
                        message=f'{task.assigned_to.get_full_name() or task.assigned_to.username} has marked task "{task.name}" as completed',
                        task=task
                    )
                
                messages.success(request, 'Update added successfully!')
                return redirect('tasks:task_detail', task_id=task.id)
        elif 'request_extension' in request.POST:
            extension_form = ExtensionRequestForm(request.POST)
            if extension_form.is_valid():
                extension_days = extension_form.cleaned_data['extension_days']
                reason = extension_form.cleaned_data['reason']
                
                # Create update for extension request
                TaskUpdate.objects.create(
                    task=task,
                    user=request.user,
                    update_type='extension',
                    message=f'Extension requested for {extension_days} days. Reason: {reason}'
                )
                
                # Update task status
                task.status = 'needs_extension'
                task.save()
                
                # Notify manager
                Notification.objects.create(
                    user=task.created_by,
                    notification_type='extension_requested',
                    message=f'{request.user.get_full_name() or request.user.username} has requested an extension of {extension_days} days for task: {task.name}',
                    task=task
                )
                
                messages.success(request, 'Extension request submitted to manager.')
                return redirect('tasks:task_detail', task_id=task.id)
    
    update_form = TaskUpdateForm()
    extension_form = ExtensionRequestForm()
    status_form = TaskStatusForm(instance=task)
    
    context = {
        'task': task,
        'updates': updates,
        'update_form': update_form,
        'extension_form': extension_form,
        'status_form': status_form,
        'can_edit': request.user == task.assigned_to,
        'is_manager': request.user.groups.filter(name='Manager').exists(),
    }
    
    return render(request, 'tasks/task_detail.html', context)

@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if not (request.user == task.created_by or request.user.groups.filter(name='Manager').exists()):
        messages.error(request, 'You do not have permission to edit this task.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            
            TaskUpdate.objects.create(
                task=task,
                user=request.user,
                update_type='progress',
                message=f'Task updated by {request.user.get_full_name() or request.user.username}'
            )
            
            messages.success(request, 'Task updated successfully!')
            return redirect('tasks:task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task, user=request.user)
    
    return render(request, 'tasks/edit_task.html', {'form': form, 'task': task})

@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if not (request.user == task.created_by or request.user.groups.filter(name='Manager').exists()):
        messages.error(request, 'You do not have permission to delete this task.')
        return redirect('tasks:dashboard')
    
    if request.method == 'POST':
        task_name = task.name
        task.delete()
        messages.success(request, f'Task "{task_name}" deleted successfully!')
        return redirect('tasks:dashboard')
    
    return render(request, 'tasks/confirm_delete.html', {'task': task})

@login_required
def add_task_update(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        form = TaskUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            update = form.save(commit=False)
            update.task = task
            update.user = request.user
            update.save()
            
            messages.success(request, 'Update added successfully!')
    
    return redirect('tasks:task_detail', task_id=task.id)

@login_required
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        form = TaskStatusForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            
            TaskUpdate.objects.create(
                task=task,
                user=request.user,
                update_type='progress',
                message=f'Status changed to {task.get_status_display()} by {request.user.get_full_name() or request.user.username}'
            )
            
            messages.success(request, 'Task status updated.')
    
    return redirect('tasks:task_detail', task_id=task.id)

@login_required
def request_extension(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if request.user != task.assigned_to:
        messages.error(request, 'Only the assigned staff can request extensions.')
        return redirect('tasks:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        form = ExtensionRequestForm(request.POST)
        if form.is_valid():
            extension_days = form.cleaned_data['extension_days']
            reason = form.cleaned_data['reason']
            
            # Create update for extension request
            TaskUpdate.objects.create(
                task=task,
                user=request.user,
                update_type='extension',
                message=f'Extension requested for {extension_days} days. Reason: {reason}'
            )
            
            # Update task status
            task.status = 'needs_extension'
            task.save()
            
            # Notify manager
            Notification.objects.create(
                user=task.created_by,
                notification_type='extension_requested',
                message=f'{request.user.get_full_name() or request.user.username} has requested an extension of {extension_days} days for task: {task.name}',
                task=task
            )
            
            messages.success(request, 'Extension request submitted to manager.')
    
    return redirect('tasks:task_detail', task_id=task.id)

@login_required
def manage_extension(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    if not request.user.groups.filter(name='Manager').exists():
        messages.error(request, 'Only managers can approve extensions.')
        return redirect('tasks:dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        extension_days = int(request.POST.get('extension_days', 0))
        
        if action == 'approve':
            task.extension_days += extension_days
            task.status = 'extension_granted'
            task.save()
            
            TaskUpdate.objects.create(
                task=task,
                user=request.user,
                update_type='approval',
                message=f'Extension of {extension_days} days approved by manager'
            )
            
            Notification.objects.create(
                user=task.assigned_to,
                notification_type='task_approved',
                message=f'Your extension request for task "{task.name}" has been approved',
                task=task
            )
            
            messages.success(request, 'Extension approved successfully.')
        elif action == 'reject':
            task.status = 'in_progress'
            task.save()
            
            TaskUpdate.objects.create(
                task=task,
                user=request.user,
                update_type='approval',
                message='Extension request rejected by manager'
            )
            
            messages.info(request, 'Extension request rejected.')
    
    return redirect('tasks:task_detail', task_id=task.id)

# tasks/views.py
@login_required
def notifications(request):
    """Handle notifications with HTMX support"""
    # Check if we should mark all as read
    if request.GET.get('mark_all_read') == 'true':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        if request.htmx:
            return HttpResponse('<div class="text-center p-3 text-muted">All notifications marked as read</div>')
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    if request.htmx:
        return render(request, 'tasks/partials/notifications_list.html', {'notifications': notifications})
    
    return render(request, 'tasks/notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.htmx:
        # Return the updated notification item
        return render(request, 'tasks/partials/notification_item.html', {'notification': notification})
    
    return JsonResponse({'status': 'success'})

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.htmx:
        return HttpResponse('<div class="text-center p-3 text-muted">All notifications marked as read</div>')
    
    return JsonResponse({'status': 'success'})

@login_required
def task_list_api(request):
    user = request.user
    status_filter = request.GET.get('status', '')
    
    if user.groups.filter(name='Manager').exists():
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(assigned_to=user)
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    tasks = tasks.order_by('-created_at')[:10]
    
    html = render(request, 'tasks/partials/task_list.html', {'tasks': tasks}).content.decode('utf-8')
    
    return JsonResponse({'html': html})

@login_required
def filter_tasks(request):
    user = request.user
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if user.groups.filter(name='Manager').exists():
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(assigned_to=user)
    
    if status:
        tasks = tasks.filter(status=status)
    if date_from:
        tasks = tasks.filter(start_date__gte=date_from)
    if date_to:
        tasks = tasks.filter(end_date__lte=date_to)
    
    context = {
        'tasks': tasks,
        'filtered': True,
        'status_filter': status,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    if request.htmx:
        return render(request, 'tasks/partials/task_table.html', context)
    
    return render(request, 'tasks/filter.html', context)

@login_required
def reports(request):
    user = request.user
    is_manager = user.groups.filter(name='Manager').exists()
    
    if not is_manager:
        messages.error(request, 'Only managers can access reports.')
        return redirect('tasks:dashboard')
    
    # Calculate statistics
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='completed').count()
    overdue_tasks = Task.objects.filter(
        end_date__lt=timezone.now().date(),
        status__in=['pending', 'in_progress']
    ).count()
    
    # Staff performance
    staff_performance = User.objects.filter(groups__name='Staff').annotate(
        total_tasks=Count('assigned_tasks'),
        completed_tasks=Count('assigned_tasks', filter=Q(assigned_tasks__status='completed')),
        overdue_tasks=Count('assigned_tasks', filter=Q(
            assigned_tasks__end_date__lt=timezone.now().date(),
            assigned_tasks__status__in=['pending', 'in_progress']
        ))
    )
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        'staff_performance': staff_performance,
        'is_manager': is_manager,
    }
    
    return render(request, 'tasks/reports.html', context)


def custom_404(request, exception=None):
    """Custom 404 error page"""
    return render(request, '404.html', status=404)

def custom_500(request):
    """Custom 500 error page"""
    return render(request, '500.html', status=500)

def test_404(request):
    """Test 404 page - only works when DEBUG=False"""
    return render(request, '404.html', status=404)

def test_500(request):
    """Test 500 page"""
    return render(request, '500.html', status=500)