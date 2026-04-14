from django.db.models import Avg, Count, F, Q
from django.utils import timezone
from annotation.models import Project, Document, Annotator, Annotation, ProjectEnrollment, ProjectLogEntry
from django.utils.timesince import timesince

def custom_dashboard_callback(request, context):
    """
    Dashboard globale: mostra lo stato di salute generale del sistema e i volumi.
    """
    
    # 1. KPI Progetti e Annotatori
    draft_projects_count = Project.objects.filter(status='DRAFT').count()
    playground_projects_count = Project.objects.filter(status='LIVE', is_published=False).count()
    launched_projects_count = Project.objects.filter(status='LIVE', is_published=True).count()
    completed_projects_count = Project.objects.filter(status='COMPLETED').count()
    
    total_annotators = Annotator.objects.count()
    
    # 5. Activity Log (Vede gli eventi di sistema)
    recent_logs_qs = ProjectLogEntry.objects.select_related('project').order_by('-timestamp')[:6]
    recent_logs = []
    for log in recent_logs_qs:
        recent_logs.append({
            'project': log.project.name,
            'action': log.action,
            'details': log.details[:50] + '...' if len(log.details) > 50 else log.details,
            'time_ago': timesince(log.timestamp) + ' fa' if log.timestamp else 'Poco fa',
            'is_launch': 'Launch' in log.action or 'Live' in log.action
        })

    # 6. Progetti Live e Lanciati (Per la colonna a destra)
    playground_qs = Project.objects.filter(status='LIVE', is_published=False)
    launched_qs = Project.objects.filter(status='LIVE', is_published=True)
    
    def serialize_project(p):
        p_total = p.documents.count()
        p_completed = p.documents.filter(current_annotations_count__gte=F('min_annotations_required')).count()
        p_pct = int((p_completed / p_total) * 100) if p_total > 0 else 0
        str_type = p.get_distribution_strategy_display().split('-')[0].strip()
        return {
            'name': p.name,
            'type': str_type,
            'status_label': 'Live' if not p.is_published else 'Launched',
            'progress': p_pct
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
