from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
import json
from ..models import ProjectEnrollment
from .utils import HighlightMedia


@admin.register(ProjectEnrollment)
class ProjectEnrollmentAdmin(ModelAdmin):
    list_display = (
        'annotator',
        'project',
        'screening_status_badge',
        'training_tasks_completed',
        'training_accuracy_display',
        'created_at',
    )
    list_filter = ('screening_status', 'project')
    search_fields = ('annotator__prolific_pid', 'project__name')
    list_select_related = ('annotator', 'project')

    readonly_fields = (
        'annotator',
        'project',
        'created_at',
        'updated_at',
        'formatted_survey_data',
    )

    fieldsets = (
        ("Enrollment", {
            "fields": ("annotator", "project", "screening_status"),
        }),
        ("Training Metrics", {
            "fields": ("training_tasks_completed", "training_accuracy"),
            "description": "Screening/training progress for this enrollment.",
        }),
        ("Survey", {
            "fields": ("formatted_survey_data",),
            "description": "Post-task survey responses.",
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

    @admin.display(description="Accuracy")
    def training_accuracy_display(self, obj):
        if obj.training_accuracy is None:
            return "-"
        return f"{obj.training_accuracy:.0%}"

    @admin.display(description="Survey Data (JSON)")
    def formatted_survey_data(self, obj):
        if not obj.survey_data:
            return format_html('<em style="color:#999">{}</em>', "No survey data.")

        try:
            json_str = json.dumps(obj.survey_data, indent=4, sort_keys=True)
            return format_html(
                '''
                <div style="border: 1px solid #e0e0e0; border-radius: 4px; overflow: hidden;">
                    <pre style="margin: 0;"><code class="json" style="padding: 15px; display: block; overflow-x: auto; max-height: 400px;">{}</code></pre>
                </div>
                ''',
                json_str
            )
        except Exception:
            return "-"
