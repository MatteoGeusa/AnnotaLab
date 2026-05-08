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
    list_filter = (HideGoldFilter, 'is_test', 'document__project', 'created_at', 'annotator')
    search_fields = ('document__text', 'annotator__prolific_pid', 'result')
    readonly_fields = ('created_at', 'formatted_result')
    exclude = ('result',)

    @admin.display(description="ID")
    def short_id(self, obj):
        return str(obj.id)[:8] + '...'

    @admin.display(description="Type", ordering='is_test')
    def annotation_type(self, obj):
        if obj.is_test:
            return mark_safe(
                '<span style="background:#f59e0b; color:white; padding:2px 8px; '
                'border-radius:4px; font-size:11px; font-weight:600;">'
                '🧪 Test</span>'
            )
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
        spans = obj.result.get('spans') or obj.result.get('span_highlight') or []
        classification = obj.result.get('classification', 'N/A')
        
        # Sort spans by starting index
        spans = sorted(spans, key=lambda x: x.get('start', 0))
        
        # Get colors from project configuration
        try:
            schema = obj.document.project.annotation_schema or {}
            components = schema.get('components', [])
            color_map = {}
            for comp in components:
                if comp.get('type') == 'span_highlight':
                    for label in comp.get('labels', []):
                        color_map[label['name']] = label.get('color', '#fbbf24')
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
        
        # Implement Overlapping Spans Visualization
        boundaries = set([0, len(text)])
        for span in spans:
            boundaries.add(span.get('start', 0))
            boundaries.add(span.get('end', 0))
            
        sorted_boundaries = sorted(list(boundaries))
        
        # Start Document Text Box
        html_parts.append('<div class="annot-container" style="line-height: 2.5;">')
        
        for i in range(len(sorted_boundaries) - 1):
            start = sorted_boundaries[i]
            end = sorted_boundaries[i+1]
            if start == end:
                continue
                
            chunk_text = text[start:end]
            
            # Find active spans for this chunk
            active_spans = []
            for span in spans:
                if span.get('start', 0) <= start and span.get('end', 0) >= end:
                    active_spans.append(span)
                    
            if not active_spans:
                html_parts.append(escape(chunk_text))
            else:
                labels_html = []
                border_shadows = []
                bg_color = None
                
                # Sort active spans predictably
                active_spans_sorted = sorted(active_spans, key=lambda x: (x.get('start', 0), -x.get('end', 0)))
                
                for idx, span in enumerate(active_spans_sorted):
                    label = span.get('label', 'Unknown')
                    color = color_map.get(label, '#fbbf24')
                    hex_color = color if str(color).startswith('#') else '#fbbf24'
                    
                    if idx == 0:
                        bg_color = f"{hex_color}33"
                        
                    # Calculate border depth
                    depth = (idx + 1) * 3
                    border_shadows.append(f"0 {depth}px 0 0 {hex_color}")
                    
                    # Only insert the label if this chunk represents the END of this specific span
                    if span.get('end', 0) == end:
                        labels_html.append(
                            f'<span class="annot-label" style="color: {hex_color}; border: 1px solid {hex_color}33;">{escape(label)}</span>'
                        )
                
                shadow_style = ", ".join(border_shadows)
                labels_joined = "".join(labels_html)
                titles = " | ".join([s.get('label', 'Unknown') for s in active_spans_sorted])
                
                html_parts.append(
                    f'<mark style="background-color: {bg_color}; box-shadow: {shadow_style}; padding: 2px 0px; border-radius: 2px;" title="{escape(titles)}">'
                    f'{escape(chunk_text)}'
                    f'{labels_joined}'
                    f'</mark>'
                )
            
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
