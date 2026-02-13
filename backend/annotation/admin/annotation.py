from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
import json
from ..models import Annotation

@admin.register(Annotation)
class AnnotationAdmin(ModelAdmin):
    list_display = ('short_id', 'document_link', 'annotator_link', 'created_at', 'seconds_to_complete')
    list_filter = ('document__project', 'created_at', 'annotator')
    search_fields = ('document__text', 'annotator__prolific_pid', 'result')
    readonly_fields = ('created_at','result')

    @admin.display(description="ID")
    def short_id(self, obj):
        return str(obj.id)[:8]+'...'

    @admin.display(description="Document")
    def document_link(self, obj):
        if not obj.document: return "-"
        url = reverse("admin:annotation_document_change", args=[obj.document.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.document))

    @admin.display(description="Annotator")
    def annotator_link(self, obj):
        if not obj.annotator: return "-"
        url = reverse("admin:annotation_annotator_change", args=[obj.annotator.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.annotator))

    def seconds_to_complete(self, obj):
        if obj.milliseconds_to_complete < 2000:
            return format_html('<span style="color: red;">{}ms</span>', obj.milliseconds_to_complete)
        return format_html('<span style="color: green;">{}ms</span>', obj.milliseconds_to_complete)

