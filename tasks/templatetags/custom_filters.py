# tasks/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def status_color(status):
    color_map = {
        'pending': 'secondary',
        'in_progress': 'info',
        'completed': 'success',
        'needs_extension': 'warning',
        'extension_granted': 'primary',
        'closed': 'dark',
    }
    return color_map.get(status, 'secondary')

@register.filter
def filter_by_week(tasks, weeks=1):
    """Filter tasks due within the next X weeks"""
    from datetime import datetime, timedelta
    today = datetime.now().date()
    future_date = today + timedelta(weeks=weeks * 7)
    return tasks.filter(end_date__range=[today, future_date])