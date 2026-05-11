from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone
from annotation.models import Project, Document, Annotator, Annotation, ProjectEnrollment, ProjectLogEntry
from django.utils.timesince import timesince

def custom_dashboard_callback(request, context):
    """
    Global dashboard: shows the general health status of the system and volumes.
    Filters data so regular users only see metrics for their projects.
    """
    
    # 0. Filter projects based on user permissions
    if request.user.is_superuser:
        user_projects = Project.objects.all()
    else:
        user_projects = Project.objects.filter(
            Q(owner=request.user) | Q(memberships__user=request.user)
        ).distinct()

    # 1. Project KPIs
    draft_projects_count = user_projects.filter(status='DRAFT').count()
    playground_projects_count = user_projects.filter(status='LIVE', is_published=False).count()
    launched_projects_count = user_projects.filter(status='LIVE', is_published=True).count()
    completed_projects_count = user_projects.filter(status='COMPLETED').count()
    
    if request.user.is_superuser:
        total_annotators = Annotator.objects.count()
    else:
        total_annotators = Annotator.objects.filter(enrollments__project__in=user_projects).distinct().count()
    
    # 5. Activity Log (System events)
    recent_logs_qs = ProjectLogEntry.objects.filter(project__in=user_projects).select_related('project').order_by('-timestamp')[:6]
    recent_logs = []
    from django.urls import reverse
    for log in recent_logs_qs:
        recent_logs.append({
            'project': log.project.name,
            'project_url': reverse('admin:project_dashboard', args=[log.project.slug]),
            'action': log.action,
            'details': log.details[:50] + '...' if len(log.details) > 50 else log.details,
            'time_ago': (timesince(log.timestamp).split(',')[0] + ' ago') if log.timestamp else 'Just now',
            'is_launch': 'Launch' in log.action or 'Live' in log.action
        })

    # 6. Live and Launched Projects (For the right column)
    playground_qs = user_projects.filter(status='LIVE', is_published=False)
    launched_qs = user_projects.filter(status='LIVE', is_published=True)
    
    def serialize_project(p):
        regular_docs = p.documents.filter(is_gold_unit=False)
        total_req = regular_docs.aggregate(total=Sum('min_annotations_required'))['total'] or 0
        total_curr = regular_docs.aggregate(total=Sum('current_annotations_count'))['total'] or 0
        p_pct = int((total_curr / total_req) * 100) if total_req > 0 else 0
        if p_pct > 100: p_pct = 100
        
        # safely handle missing distribution strategy
        str_type = p.get_distribution_strategy_display().split('-')[0].strip() if p.distribution_strategy else "Unknown"
        
        return {
            'id': p.id,
            'name': p.name,
            'type': str_type,
            'status_label': 'Live' if not p.is_published else 'Launched',
            'progress': p_pct,
            'description': p.description,
            'url': reverse('admin:project_dashboard', args=[p.slug])
        }

    playground_projects = [serialize_project(p) for p in playground_qs]
    launched_projects = [serialize_project(p) for p in launched_qs]
        
    context.update({
        "draft_projects_count": draft_projects_count,
        "playground_projects_count": playground_projects_count,
        "launched_projects_count": launched_projects_count,
        "completed_projects_count": completed_projects_count,
        "total_annotators": total_annotators,
        "recent_logs": recent_logs,
        "playground_projects": playground_projects,
        "launched_projects": launched_projects
    })
    
    return context
