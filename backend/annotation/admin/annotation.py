from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html, mark_safe, escape
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
import json
from ..models import Annotation


class HideGoldFilter(admin.SimpleListFilter):
    title = 'Task Category'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return (
            ('regular', 'Regular Tasks'),
            ('gold', 'Gold Tasks'),
        )

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
    readonly_fields = ('created_at', 'formatted_result')
    exclude = ('result',)

    @admin.display(description="ID")
    def short_id(self, obj):
        return str(obj.id)[:8] + '...'

    @admin.display(description="Type", ordering='document__is_gold_unit')
    def annotation_type(self, obj):
        if obj.document and obj.document.is_gold_unit:
            return mark_safe(
                '<span style="background:#fbbf24; color:#1f2937; padding:2px 8px; '
                'border-radius:4px; font-size:11px; font-weight:600;">'
                '🏆 Gold Task</span>'
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
        if obj.document.is_gold_unit:
            url = reverse("admin:annotation_goldunitproxy_change", args=[obj.document.id])
        else:
            url = reverse("admin:annotation_documentproxy_change", args=[obj.document.id])
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

    @admin.display(description="Annotated Results Visualization")
    def formatted_result(self, obj):
        if not obj.result:
            return "-"
            
        text = obj.document.text if obj.document else ""
        spans = obj.result.get('spans', [])
        classification = obj.result.get('classification', 'N/A')
        
        # Sort spans by starting index
        spans = sorted(spans, key=lambda x: x.get('start', 0))
        
        # Get colors from project configuration
        try:
            project_labels = obj.document.project.task_type_config.get('span_labels', [])
            color_map = {label['name']: label.get('color', '#fbbf24') for label in project_labels}
        except Exception:
            color_map = {}
            
        last_idx = 0
        html_parts = []
        
        # Add CSS styles for dark mode compatibility
        html_parts.append(
            '<style>'
            '.annot-class-box { margin-bottom: 20px; padding: 12px 16px; background: #e0f2fe; border: 1px solid #bae6fd; border-radius: 8px; font-size: 14px; color: #0369a1; }'
            '.annot-class-val { background: white; padding: 4px 10px; border-radius: 6px; font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }'
            '.annot-container { line-height: 2.2; font-size: 16px; padding: 24px; border: 1px solid #e5e7eb; border-radius: 8px; background: white; color: #374151; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }'
            '.annot-details { margin-top: 20px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }'
            '.annot-summary { cursor: pointer; padding: 12px 16px; background: #f9fafb; color: #4b5563; font-size: 14px; font-weight: 500; user-select: none; }'
            '.annot-label { display: inline-block; font-size: 0.70rem; font-weight: 700; margin-left: 6px; text-transform: uppercase; background: white; padding: 2px 6px; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); position: relative; top: -1px; }'
            'html[data-theme="dark"] .annot-class-box, .dark .annot-class-box { background: #0c4a6e; border-color: #075985; color: #bae6fd; }'
            'html[data-theme="dark"] .annot-class-val, .dark .annot-class-val { background: #082f49; color: #e0f2fe; }'
            'html[data-theme="dark"] .annot-container, .dark .annot-container { background: #1f2937; border-color: #374151; color: #d1d5db; box-shadow: none; }'
            'html[data-theme="dark"] .annot-details, .dark .annot-details { border-color: #374151; }'
            'html[data-theme="dark"] .annot-summary, .dark .annot-summary { background: #111827; color: #9ca3af; }'
            'html[data-theme="dark"] .annot-label, .dark .annot-label { background: #374151; color: #e5e7eb; box-shadow: none; border: 1px solid #4b5563 !important; }'
            'html[data-theme="dark"] mark, .dark mark { color: #f9fafb !important; }'
            '</style>'
        )

        # Add Classification Badge
        html_parts.append(
            f'<div class="annot-class-box">'
            f'<strong style="margin-right: 8px;">Classification:</strong>'
            f'<span class="annot-class-val">{escape(str(classification))}</span>'
            f'</div>'
        )
        
        # Start Document Text Box
        html_parts.append('<div class="annot-container">')
        
        for span in spans:
            start = span.get('start', 0)
            end = span.get('end', 0)
            label = span.get('label', 'Unknown')
            color = color_map.get(label, '#fbbf24')
            hex_color = color if str(color).startswith('#') else '#fbbf24'
            
            # Add unannotated text before this span
            if start > last_idx:
                html_parts.append(escape(text[last_idx:start]))
                
            # Add annotated text
            span_text = text[start:end]
            html_parts.append(
                f'<mark style="background-color: {hex_color}33; border-bottom: 3px solid {hex_color}; padding: 4px 6px; border-radius: 4px; margin: 0 2px;" title="{escape(label)}">'
                f'{escape(span_text)}'
                f'<span class="annot-label" style="color: {hex_color}; border: 1px solid {hex_color}33;">{escape(label)}</span>'
                f'</mark>'
            )
            last_idx = end
            
        # Add remaining text
        if last_idx < len(text):
            html_parts.append(escape(text[last_idx:]))
            
        html_parts.append('</div>')
        
        # Add raw JSON toggle
        raw_json = json.dumps(obj.result, indent=2)
        html_parts.append(
            f'<details class="annot-details">'
            f'<summary class="annot-summary">View Raw JSON Payload</summary>'
            f'<div style="padding: 16px; background: #111827; overflow-x: auto;">'
            f'<pre style="color: #6ee7b7; font-size: 13px; font-family: monospace; margin: 0;">{escape(raw_json)}</pre>'
            f'</div>'
            f'</details>'
        )
        
        return mark_safe("".join(html_parts))

    def changelist_view(self, request, extra_context=None):
        """Redirect if no project filter is active."""
        if 'document__project__id__exact' not in request.GET and 'document__project__id' not in request.GET:
            self.message_user(request, "Select a project first to view its annotations.", messages.WARNING)
            return HttpResponseRedirect(reverse('admin:annotation_project_changelist'))
        
        return super().changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, request):
        """Hides this model from the sidebar/index."""
        return False
