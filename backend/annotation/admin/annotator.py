from django.contrib import admin, messages
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode
from django.db.models import ProtectedError
import json
from ..models import Annotator
from .utils import HighlightMedia

@admin.register(Annotator)
class AnnotatorAdmin(ModelAdmin):
    list_display = ('prolific_pid', 'created_at', 'view_work_link')
    search_fields = ('prolific_pid',)
    
    # created_at is read-only to prevent editing
    readonly_fields = ('created_at', 'formatted_metadata')

    fieldsets = (
        ("Annotator Profile", {
            "fields": ("prolific_pid", "created_at")
        }),
        ("Onboarding Status", {
            "fields": ("consent_accepted", "onboarding_completed"),
            "description": "Manage annotator's progression status."
        }),
        ("Metadata", {
            "fields": ("formatted_metadata",),
            "description": "JSON metadata associated with this worker (e.g. Group, Demographics)."
        }),
    )
    
    # CSS/JS for Highlight.js syntax highlighting
    Media = HighlightMedia

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
