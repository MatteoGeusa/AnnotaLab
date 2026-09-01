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
from django.core.exceptions import ObjectDoesNotExist
from ..models import Document, DocumentProxy, GoldUnitProxy, Project

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

    class Media:
        js = ('js/admin_project.js',)

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj is None and not request.user.is_superuser:
            from django.contrib import messages
            messages.error(request, "⚠️ Access Denied: You do not have permissions to view this document.")
        return obj

    @admin.display(description="External ID", ordering="external_id")
    def external_id_display(self, obj):
        return obj.external_id

    change_list_template = 'admin/annotation/mace_changelist.html'

    def changelist_view(self, request, extra_context=None):
        """Redirect if no project filter is active and inject MACE URL."""
        project_id = request.GET.get('project__id__exact') or request.GET.get('project__id')
        
        if not project_id:
            self.message_user(request, "Select a project first to view its records.", messages.WARNING)
            return HttpResponseRedirect(reverse('admin:annotation_project_changelist'))
        
        extra_context = extra_context or {}
        try:
            project = Project.objects.get(pk=project_id)
            extra_context['mace_run_url'] = reverse('admin:project_run_mace', args=[project_id])
            extra_context['mace_project_name'] = project.name
            print(f"DEBUG: MACE URL for project {project_id}: {extra_context['mace_run_url']}")
        except (ObjectDoesNotExist, ValueError) as e:
            print(f"DEBUG: Failed to get project {project_id}: {e}")
            pass

        return super().changelist_view(request, extra_context=extra_context)

    def has_module_permission(self, request):
        return False

@admin.register(DocumentProxy)
class DocumentProxyAdmin(BaseDocumentAdmin):
    list_display = ('external_id_display', 'short_text', 'project', 'is_gold_unit_display', 'current_annotations_count', 'is_completed', 'mace_gold_display', 'mace_confidence_display')
    list_filter = ('project', 'is_gold_unit')

    @admin.display(boolean=True, description="Gold Unit?")
    def is_gold_unit_display(self, obj):
        return obj.is_gold_unit

    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        from django.db.models import Q
        return qs.filter(
            project__in=Project.objects.filter(
                Q(owner=request.user) | Q(memberships__user=request.user)
            )
        ).distinct()

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
        qs = super().get_queryset(request).filter(is_gold_unit=True)
        if request.user.is_superuser:
            return qs
        from django.db.models import Q
        return qs.filter(
            project__in=Project.objects.filter(
                Q(owner=request.user) | Q(memberships__user=request.user)
            )
        ).distinct()

    @admin.display(description="Gold Solution")
    def gold_preview(self, obj):
        if not obj.gold_solution: return "-"
        return obj.gold_solution.get('classification', 'N/A')

    fieldsets = (
        ("Gold Unit Content", {"fields": ("external_id", "text")}),
        ("Context", {"fields": ("project", "metadata")}),
        ("Quality Control", {"fields": ("gold_solution",)})
    )

