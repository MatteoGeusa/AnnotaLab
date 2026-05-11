from django.contrib import admin, messages
from unfold.admin import ModelAdmin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.utils.http import urlencode
from django.db.models import ProtectedError
import json
from ..models import Annotator, Project
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
        test_q = Q(is_test=True) | Q(metadata__has_key='is_test', metadata__is_test="true")
        
        if val == 'real':
            return queryset.exclude(test_q)
        if val == 'test':
            return queryset.filter(test_q)
        return queryset


@admin.register(Annotator)
class AnnotatorAdmin(ModelAdmin):
    list_display = ('prolific_pid', 'annotator_type', 'created_at', 'view_work_link')
    list_filter = (WorkerTypeFilter, 'created_at')
    search_fields = ('prolific_pid',)
    
    # created_at is read-only to prevent editing
    readonly_fields = ('created_at', 'formatted_metadata')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        from django.db.models import Q
        return qs.filter(
            enrollments__project__in=Project.objects.filter(
                Q(owner=request.user) | Q(memberships__user=request.user)
            )
        ).distinct()

    fieldsets = (
        ("Annotator Profile", {
            "fields": ("prolific_pid", "created_at")
        }),

        ("Metadata", {
            "fields": ("formatted_metadata",),
            "description": "JSON metadata associated with this worker (e.g. Group, Demographics)."
        }),
    )
    
    # CSS/JS for Highlight.js syntax highlighting
    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/stackoverflow-light.min.css',)
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js',
            'js/admin_highlight_init.js',
            'js/admin_project.js', # For popups
        )

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj is None and not request.user.is_superuser:
            from django.contrib import messages
            messages.error(request, "⚠️ Access Denied: You do not have permissions to view this worker's profile.")
        return obj

    @admin.display(description="Type")
    def annotator_type(self, obj):
        is_test = obj.is_test or str(obj.metadata.get('is_test', 'false')).lower() == 'true'
        if is_test:
            return mark_safe(
                '<span style="background:#f59e0b; color:white; padding:2px 8px; '
                'border-radius:4px; font-size:11px; font-weight:600;">'
                '🧪 Test</span>'
            )
        return mark_safe(
            '<span style="background:#059669; color:white; padding:2px 8px; '
            'border-radius:4px; font-size:11px; font-weight:600;">'
            '👥 Real</span>'
        )

    @admin.display(description="Metadata (JSON)")
    def formatted_metadata(self, obj):
        if not obj or not obj.metadata:
            return format_html('<em style="color:#999">{}</em>', "No metadata present.")
        
        try:
            json_str = json.dumps(obj.metadata, indent=4, sort_keys=True)
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

    @admin.display(description="History")
    def view_work_link(self, obj):
        # Safety check: don't show link if the object has no ID yet (e.g. during creation)
        if not obj or not obj.id:
            return "-"
            
        count = obj.annotations.count()
        
        # Generazione URL sicura
        base_url = reverse("admin:annotation_annotation_changelist")
        query_string = urlencode({"annotator__id": f"{obj.id}"})
        full_url = f"{base_url}?{query_string}"
        
        return format_html('<a href="{}" style="font-weight:bold;">View {} Tasks</a>', full_url, count)

    def delete_model(self, request, obj):
        try:
            obj.delete()
        except ProtectedError:
            count = obj.annotations.count()
            messages.error(
                request,
                f'Cannot delete "{obj.prolific_pid}": '
                f'this annotator has {count} annotation(s). '
                f'Delete the annotations first, then retry.'
            )

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            self.delete_model(request, obj)
