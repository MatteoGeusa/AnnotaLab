from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
import json
from ..models import Annotation


class HideGoldFilter(admin.SimpleListFilter):
    title = 'Task Category'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return (
            ('all', 'Show All (Regular + Gold)'),
            ('regular', 'Hide Gold Tasks (Only Regular)'),
            ('gold', 'Only Gold Tasks'),
        )

    def value(self):
        v = super().value()
        if v is None:
            return 'regular'
        return v

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'regular':
            return queryset.filter(document__is_gold_unit=False)
        if val == 'gold':
            return queryset.filter(document__is_gold_unit=True)
        return queryset


@admin.register(Annotation)
class AnnotationAdmin(ModelAdmin):
    list_display = ('short_id', 'annotation_type', 'document_link', 'annotator_link', 'created_at', 'seconds_to_complete')
    list_filter = (HideGoldFilter, 'document__project', 'created_at', 'annotator')
    search_fields = ('document__text', 'annotator__prolific_pid', 'result')
    readonly_fields = ('created_at', 'result')

    @admin.display(description="ID")
    def short_id(self, obj):
        return str(obj.id)[:8] + '...'

    @admin.display(description="Type", ordering='document__is_gold_unit')
    def annotation_type(self, obj):
        if obj.document and obj.document.is_gold_unit:
            return mark_safe(
                '<span style="background:#7c3aed; color:white; padding:2px 8px; '
                'border-radius:4px; font-size:11px; font-weight:600;">'
                '🏋️ Training</span>'
            )
        return mark_safe(
            '<span style="background:#059669; color:white; padding:2px 8px; '
            'border-radius:4px; font-size:11px; font-weight:600;">'
            '📝 Regular</span>'
        )

    @admin.display(description="Document")
    def document_link(self, obj):
        if not obj.document:
            return "-"
        url = reverse("admin:annotation_document_change", args=[obj.document.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.document))

    @admin.display(description="Annotator")
    def annotator_link(self, obj):
        if not obj.annotator:
            return "-"
        url = reverse("admin:annotation_annotator_change", args=[obj.annotator.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.annotator))

    @admin.display(description="Time")
    def seconds_to_complete(self, obj):
        if not obj.milliseconds_to_complete:
            return "-"
        if obj.milliseconds_to_complete < 5000:
            return format_html(
                '<span style="color: #ef4444; font-weight:600;">{}ms</span>',
                obj.milliseconds_to_complete
            )
        return format_html(
            '<span style="color: #22c55e;">{}ms</span>',
            obj.milliseconds_to_complete
        )
