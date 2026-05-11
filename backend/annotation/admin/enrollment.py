from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from ..models import ProjectEnrollment, Project
from .utils import HighlightMedia


class WorkerTypeFilter(admin.SimpleListFilter):
    title = 'Worker Type'
    parameter_name = 'worker_type'

    def lookups(self, request, model_admin):
        return (
            ('real', 'Real Workers'),
            ('test', 'Test Workers'),
        )

    def queryset(self, request, queryset):
        from django.db.models import Q
        val = self.value()
        # A worker is test if is_test=True OR metadata has {"is_test": "true"}
        test_q = Q(annotator__is_test=True) | Q(annotator__metadata__has_key='is_test', annotator__metadata__is_test="true")
        
        if val == 'real':
            return queryset.exclude(test_q)
        if val == 'test':
            return queryset.filter(test_q)
        return queryset


@admin.register(ProjectEnrollment)
class ProjectEnrollmentAdmin(ModelAdmin):
    list_display = (
        'annotator',
        'worker_type_badge',
        'project',
        'status_badge',
        'gold_tasks_completed_display',
        'gold_accuracy_display',
        'mace_competence_display',
        'exclude_from_distribution',
        'created_at',
    )
    list_filter = ('status', 'project', WorkerTypeFilter, 'exclude_from_distribution')
    search_fields = ('annotator__prolific_pid', 'project__name')
    list_select_related = ('annotator', 'project')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        from django.db.models import Q
        return qs.filter(
            project__in=Project.objects.filter(
                Q(owner=request.user) | Q(memberships__user=request.user)
            )
        ).distinct()

    readonly_fields = (
        'annotator',
        'project',
        'created_at',
        'updated_at',
        'gold_tasks_completed_display',
        'mace_competence_score',
        'mace_spam_bias',
    )

    fieldsets = (
        ("Enrollment", {
            "fields": ("annotator", "project", "status", "exclude_from_distribution"),
        }),
        ("Progression Status", {
            "fields": ("consent_accepted", "screening_completed", "codebook_completed", "onboarding_completed"),
            "description": "Pre-task progression steps for this specific project.",
        }),
        ("MACE Reliability Evaluation", {
            "fields": ("mace_competence_score", "mace_spam_bias"),
            "description": "Quality metrics estimated by the MACE algorithm based on consensus patterns (unsupervised).",
        }),
        ("Gold Task Metrics", {
            "fields": ("gold_tasks_completed_display", "gold_accuracy"),
            "description": "Quality metrics based on Gold Units (supervised).",
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    # CSS/JS for Highlight.js syntax highlighting
    class Media:
        js = ('js/admin_project.js',)

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj is None and not request.user.is_superuser:
            from django.contrib import messages
            messages.error(request, "⚠️ Access Denied: You do not have permissions to view this enrollment.")
        return obj

    @admin.display(description="Type")
    def worker_type_badge(self, obj):
        annotator = obj.annotator
        is_test = annotator.is_test or str(annotator.metadata.get('is_test', 'false')).lower() == 'true'
        if is_test:
            return mark_safe(
                '<span style="background:#0891b2; color:white; padding:2px 8px; '
                'border-radius:4px; font-size:11px; font-weight:600;">'
                'Tester</span>'
            )
        return mark_safe(
            '<span style="background:#2563eb; color:white; padding:2px 8px; '
            'border-radius:4px; font-size:11px; font-weight:600;">'
            'Worker</span>'
        )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            'PENDING': '#f0ad4e',   # amber
            'ACTIVE': '#5cb85c',    # green
            'EXCLUDED': '#d9534f',  # red
            'COMPLETED': '#5bc0de', # blue
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; '
            'border-radius:4px; font-size:11px; font-weight:bold;">{}</span>',
            color, obj.status
        )

    @admin.display(description="Gold Accuracy")
    def gold_accuracy_display(self, obj):
        if obj.gold_accuracy is None:
            return "-"
        return f"{obj.gold_accuracy:.0%}"

    @admin.display(description="Gold Tasks Completed")
    def gold_tasks_completed_display(self, obj):
        return obj.gold_tasks_completed

    @admin.display(description="MACE Score", ordering="mace_competence_score")
    def mace_competence_display(self, obj):
        if obj.mace_competence_score is None:
            return "-"
        
        # Color code: red for < 0.3, orange for < 0.6, green for >= 0.6
        score = obj.mace_competence_score
        if score >= 0.6:
            color = "#10b981" # Green
        elif score >= 0.3:
            color = "#f59e0b" # Orange
        else:
            color = "#ef4444" # Red
            
        formatted_score = f"{score:.2f}"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color, formatted_score
        )

    def changelist_view(self, request, extra_context=None):
        """Redirect if no project filter is active."""
        if 'project__id__exact' not in request.GET and 'project__id' not in request.GET:
            self.message_user(request, "Select a project first to view assignments.", messages.WARNING)
            return HttpResponseRedirect(reverse('admin:annotation_project_changelist'))
        
        return super().changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, request):
        """Hides this model from the sidebar/index."""
        return False
