from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from ..models import ProjectEnrollment
from .utils import HighlightMedia


@admin.register(ProjectEnrollment)
class ProjectEnrollmentAdmin(ModelAdmin):
    list_display = (
        'annotator',
        'project',
        'screening_status_badge',
        'gold_tasks_completed_display',
        'training_accuracy_display',
        'exclude_from_distribution',
        'created_at',
    )
    list_filter = ('screening_status', 'project', 'exclude_from_distribution')
    search_fields = ('annotator__prolific_pid', 'project__name')
    list_select_related = ('annotator', 'project')

    readonly_fields = (
        'annotator',
        'project',
        'created_at',
        'updated_at',
        'gold_tasks_completed_display',
    )

    fieldsets = (
        ("Enrollment", {
            "fields": ("annotator", "project", "screening_status", "exclude_from_distribution"),
        }),
        ("Workload", {
            "fields": ("target_tasks",),
            "description": "How many tasks this specific user must complete for this project.",
        }),
        ("Gold Task Metrics", {
            "fields": ("gold_tasks_completed_display", "training_accuracy"),
            "description": "Screening progress based on Gold Units.",
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    # CSS/JS for Highlight.js syntax highlighting
    Media = HighlightMedia

    @admin.display(description="Status")
    def screening_status_badge(self, obj):
        colors = {
            'PENDING': '#f0ad4e',  # amber
            'PASSED': '#5cb85c',   # green
            'FAILED': '#d9534f',   # red
        }
        color = colors.get(obj.screening_status, '#999')
        return format_html(
            '<span style="background:{}; color:#fff; padding:3px 8px; '
            'border-radius:4px; font-size:11px; font-weight:bold;">{}</span>',
            color, obj.screening_status
        )

    @admin.display(description="Gold Tasks Accuracy")
    def training_accuracy_display(self, obj):
        if obj.training_accuracy is None:
            return "-"
        return f"{obj.training_accuracy:.0%}"

    @admin.display(description="Gold Tasks Completed")
    def gold_tasks_completed_display(self, obj):
        return obj.training_tasks_completed

    def changelist_view(self, request, extra_context=None):
        """Redirect if no project filter is active."""
        if 'project__id__exact' not in request.GET and 'project__id' not in request.GET:
            self.message_user(request, "Select a project first to view assignments.", messages.WARNING)
            return HttpResponseRedirect(reverse('admin:annotation_project_changelist'))
        
        return super().changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, request):
        """Hides this model from the sidebar/index."""
        return False
