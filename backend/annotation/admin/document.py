from django.contrib import admin
from import_export import resources
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from ..models import Document

class DocumentResource(resources.ModelResource):
    class Meta:
        model = Document
        fields = ('id', 'text', 'external_id', 'project')

@admin.register(Document)
class DocumentAdmin(ModelAdmin, ImportExportModelAdmin):
    resource_class = DocumentResource
    list_display = ('external_id', 'short_text', 'project', 'current_annotations_count', 'is_gold_unit', 'is_completed')
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
