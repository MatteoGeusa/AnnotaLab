from django.contrib import admin
from import_export import resources
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin
from django.utils.html import format_html
from django.db.models import IntegerField
from django.db.models.functions import Cast
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from ..models import Document, DocumentProxy, GoldUnitProxy

class DocumentResource(resources.ModelResource):
    class Meta:
        model = Document
        fields = ('id', 'text', 'external_id', 'project')

class BaseDocumentAdmin(ModelAdmin, ImportExportModelAdmin):
    """Base logic for Document administration."""
    resource_class = DocumentResource
    search_fields = ('text', 'external_id', 'metadata')
    
    @admin.display(description="Text Preview")
    def short_text(self, obj):
        return obj.text[:80] + "..." if len(obj.text) > 80 else obj.text

    @admin.display(description="External ID", ordering="external_id")
    def external_id_display(self, obj):
        return obj.external_id

    def changelist_view(self, request, extra_context=None):
        """Redirect if no project filter is active."""
        if 'project__id__exact' not in request.GET and 'project__id' not in request.GET:
            self.message_user(request, "Select a project first to view its records.", messages.WARNING)
            return HttpResponseRedirect(reverse('admin:annotation_project_changelist'))
        return super().changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, request):
        return False

@admin.register(DocumentProxy)
class DocumentProxyAdmin(BaseDocumentAdmin):
    list_display = ('external_id_display', 'short_text', 'project', 'current_annotations_count', 'is_completed', 'mace_gold_display', 'mace_confidence_display')
    list_filter = ('project',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_gold_unit=False)

    @admin.display(boolean=True, description="Completed?")
    def is_completed(self, obj):
        return obj.current_annotations_count >= obj.min_annotations_required

    @admin.display(description="MACE Label")
    def mace_gold_display(self, obj):
        if obj.mace_gold_label:
            return obj.mace_gold_label
        return "-"
        
    @admin.display(description="MACE Confidence", ordering="mace_confidence")
    def mace_confidence_display(self, obj):
        if obj.mace_confidence is None:
            return "-"
        
        score = obj.mace_confidence
        if score >= 0.8:
            color = "#10b981" # Green
        elif score >= 0.5:
            color = "#f59e0b" # Orange
        else:
            color = "#ef4444" # Red
            
        formatted_score = f"{score:.2f}"
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color, formatted_score
        )

    fieldsets = (
        ("Document Content", {"fields": ("external_id", "text")}),
        ("Context & Metadata", {"fields": ("project", "metadata")}),
        ("MACE Estimations", {"fields": ("mace_gold_label", "mace_confidence")}),
        ("Annotation Strategy", {"fields": ("min_annotations_required",)})
    )

@admin.register(GoldUnitProxy)
class GoldUnitProxyAdmin(BaseDocumentAdmin):
    list_display = ('external_id_display', 'short_text', 'project', 'gold_preview')
    list_filter = ('project',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_gold_unit=True)

    @admin.display(description="Gold Solution")
    def gold_preview(self, obj):
        if not obj.gold_solution: return "-"
        return obj.gold_solution.get('classification', 'N/A')

    fieldsets = (
        ("Gold Unit Content", {"fields": ("external_id", "text")}),
        ("Context", {"fields": ("project", "metadata")}),
        ("Quality Control", {"fields": ("gold_solution",)})
    )

