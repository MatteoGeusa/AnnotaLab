from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
import json
from ..models import Annotation

@admin.register(Annotation)
class AnnotationAdmin(ModelAdmin):
    list_display = ('short_id', 'document_link', 'annotator_link', 'created_at', 'milliseconds_to_complete')
    list_filter = ('document__project', 'created_at', 'annotator')
    search_fields = ('document__text', 'annotator__prolific_pid', 'result')
    readonly_fields = ('created_at', 'formatted_result')
    exclude = ('result',)

    # Configurazione CSS/JS per Highlight.js
    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/stackoverflow-light.min.css',)
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js',
            'js/admin_highlight_init.js',
        )

    @admin.display(description="ID")
    def short_id(self, obj):
        return str(obj.id)[:8]

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

    @admin.display(description="Result (JSON)")
    def formatted_result(self, obj):
        if not obj.result: return "-"
        json_str = json.dumps(obj.result, indent=2, sort_keys=True)
        return format_html(
            '<pre style="margin:0;"><code class="json" style="max-height: 300px; overflow: auto; font-size: 12px;">{}</code></pre>',
            json_str
        )
