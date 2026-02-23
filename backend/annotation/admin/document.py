from django.contrib import admin
from import_export import resources
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from ..models import Document

class DocumentResource(resources.ModelResource):
    class Meta:
        model = Document
        fields = ('id', 'text', 'external_id', 'project')

@admin.register(Document)
class DocumentAdmin(ModelAdmin, ImportExportModelAdmin):
    resource_class = DocumentResource
    list_display = ('external_id_numeric', 'short_text', 'project', 'current_annotations_count', 'is_gold_unit', 'is_completed')
    list_filter = ('project', 'is_gold_unit', 'min_annotations_required')
    search_fields = ('text', 'external_id', 'metadata')
    

    fieldsets = (
        ("Document Content", {
            "fields": (
                "external_id",  
                "text",         
            ),
            "description": "The main content that will be shown to annotators."
        }),
        ("Context & Metadata", {
            "fields": (
                "project",
                "metadata",     
            ),
        }),
        ("Annotation Strategy", {
            "fields": (
                "min_annotations_required", "is_gold_unit", "gold_solution",       
            ),
            "description": "Define if this is a quality control test (Gold Unit) or a standard document."
        }),
    )

    @admin.display(description="Text Preview")
    def short_text(self, obj):
        return obj.text[:80] + "..." if len(obj.text) > 80 else obj.text

    @admin.display(boolean=True, description="Completed?")
    def is_completed(self, obj):
        return obj.current_annotations_count >= obj.min_annotations_required

    def get_queryset(self, request):
        """Annotate the queryset with a numeric version of external_id for sorting."""
        qs = super().get_queryset(request)
        return qs.annotate(
            external_id_num=Cast('external_id', output_field=IntegerField())
        )

    @admin.display(description="External ID", ordering="external_id_num")
    def external_id_numeric(self, obj):
        return obj.external_id

    def changelist_view(self, request, extra_context=None):
        """Redirect if no project filter is active."""
        if 'project__id__exact' not in request.GET and 'project__id' not in request.GET:
            self.message_user(request, "Select a project first to view its documents.", messages.WARNING)
            return HttpResponseRedirect(reverse('admin:annotation_project_changelist'))
        
        return super().changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, request):
        """Hides this model from the sidebar/index."""
        return False
