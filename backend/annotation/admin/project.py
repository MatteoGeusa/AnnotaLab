from django.contrib import admin
from django.shortcuts import render, get_object_or_404
from django.db.models import F, Sum, Min, Q
from django import forms
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin, TabularInline
from django.utils.html import format_html, mark_safe
from django.urls import reverse, path
from django.utils.http import urlencode
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
import json
import yaml
import re
from ..models import Project, Annotation, ProjectLogEntry
from ..services import parse_json_upload, parse_yaml_upload, process_uploaded_dataset, ProjectService
from ..schema_validator import validate_gold_solution
from ..mace_service import run_mace_for_project

class ProjectAdminForm(forms.ModelForm):
    """
    Custom form that adds non-model file inputs for uploading JSON configs.
    The uploaded file is parsed and stored directly into the JSONField on save.
    """
    upload_task_config = forms.FileField(
        required=False,
        label="Upload Task Config (YAML)",
        help_text="Upload a YAML (or JSON) file to overwrite the Task configuration (Labels, Questions)."
    )
    upload_screening_config = forms.FileField(
        required=False,
        label="Upload Screening Config (YAML)",
        help_text="Upload a YAML (or JSON) file to configure the screening questionnaire (demographics, etc.)."
    )
    upload_codebook_content = forms.FileField(
        required=False,
        label="Upload Codebook (Markdown)",
        help_text="Upload a .md file to overwrite the theoretical/practical background."
    )
    upload_instructions_content = forms.FileField(
        required=False,
        label="Upload Instructions (Markdown)",
        help_text="Upload a .md file for task instructions shown before the practice task."
    )
    upload_practice_task_config = forms.FileField(
        required=False,
        label="Upload Practice Task (YAML)",
        help_text="Upload a YAML (or JSON) file with the practice task (text, gold_solution, hints)."
    )
    upload_informed_consent_content = forms.FileField(
        required=False,
        label="Upload Informed Consent (Markdown)",
        help_text="Upload a .md file to overwrite the informed consent text shown to participants before the task."
    )

    class Meta:
        model = Project
        fields = '__all__'

    def clean(self):
        import yaml
        cleaned_data = super().clean()
        documents_file = cleaned_data.get('documents_file')
        status = cleaned_data.get('status')

        fields_to_validate_positive = [
            'gold_injection_frequency', 
            'min_accuracy_required', 
            'min_gold_before_eval',
        ]
        fields_to_validate_strictly_positive = [
            'min_annotations_per_doc', 
            'max_annotations_per_doc', 
            'block_size', 
            'annotators_per_block'
        ]

        for field in fields_to_validate_positive:
            val = cleaned_data.get(field)
            if val is not None and val < 0:
                self.add_error(
                    field, 
                    "Invalid input: This parameter cannot be less than 0."
                )
                
        for field in fields_to_validate_strictly_positive:
            val = cleaned_data.get(field)
            if val is not None and val <= 0:
                self.add_error(
                    field, 
                    "Invalid input: This parameter must be strictly greater than 0."
                )

        min_annot = cleaned_data.get('min_annotations_per_doc')
        max_annot = cleaned_data.get('max_annotations_per_doc')
        if min_annot and max_annot and max_annot < min_annot:
            self.add_error(
                'max_annotations_per_doc',
                "Hard Cap (Max) cannot be lower than the Target (Min) annotations per document."
            )

        # ── LIVE status: requires a dataset ────────────────────────────────
        if status == 'LIVE':
            has_existing_docs = self.instance.documents.filter(is_gold_unit=False).exists() if self.instance.pk else False
            if not has_existing_docs and not documents_file:
                self.add_error('status',
                    "Cannot Set to LIVE: No dataset found. "
                    "Please upload a .jsonl file in 'Task Configuration' before setting the project status to Live."
                )

        # ── Cross-check: practice task gold_solution vs annotation_schema ──
        # Only runs when practice task is enabled AND a file is being uploaded.
        enable_practice = cleaned_data.get('enable_practice_task', True)
        task_config_file    = cleaned_data.get('upload_task_config')
        practice_task_file  = cleaned_data.get('upload_practice_task_config')

        if not enable_practice:
            return cleaned_data  # practice task disabled — skip all cross-validation

        def _parse_yaml_file(file_obj):
            """Parse an uploaded file as YAML, return dict or None on parse failure."""
            if not file_obj:
                return None
            try:
                file_obj.seek(0)
                content = file_obj.read().decode('utf-8')
                file_obj.seek(0)   # rewind so save_model can read it again
                return yaml.safe_load(content)
            except Exception:
                return None

        # Determine which schema to validate against:
        # 1. A newly uploaded schema (takes priority)
        # 2. The existing schema already in the DB
        if task_config_file:
            new_schema = _parse_yaml_file(task_config_file)
        elif self.instance and self.instance.pk:
            new_schema = self.instance.annotation_schema or {}
        else:
            new_schema = {}

        # Determine which practice task to validate:
        if practice_task_file:
            new_practice = _parse_yaml_file(practice_task_file)
        elif self.instance and self.instance.pk:
            new_practice = self.instance.practice_task_config or {}
        else:
            new_practice = {}

        if new_schema and new_practice:
            gold_sol = new_practice.get('gold_solution')
            if gold_sol:
                from ..schema_validator import validate_gold_solution
                errs, _ = validate_gold_solution(gold_sol, new_schema)
                if errs:
                    raise forms.ValidationError(
                        "Practice task gold_solution is incompatible with the annotation schema — "
                        "fix the practice task or the schema before saving:\n"
                        + "\n".join(f"• {e}" for e in errs)
                    )

        return cleaned_data

class ProjectLogInline(TabularInline):
    model = ProjectLogEntry
    extra = 0
    readonly_fields = ('timestamp', 'action', 'details')
    can_delete = False
    tab = True

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    # Columns visible in the project list view
    list_display = ('name_link', 'simple_status', 'completion_progress', 'stats_summary', 'created_at')
    list_filter = ('status', 'is_published', 'created_at')
    search_fields = ('name', 'slug')
    @admin.display(description="Project Name", ordering='name')
    def name_link(self, obj):
        url = reverse('admin:project_dashboard', args=[obj.slug])
        suffix = " 🔒" if obj.is_published else ""
        return format_html('<a href="{}" style="font-weight:700; text-decoration:none; color:#3b82f6;">{}{}</a>', url, obj.name, suffix)

    @admin.display(description="Status", ordering='status')
    def simple_status(self, obj):
        status_colors = {
            'DRAFT': '#64748b', 
            'LIVE': '#10b981',   
            'PAUSED': '#f59e0b', 
            'COMPLETED': '#3b82f6', 
        }
        color = status_colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 700; text-transform: uppercase;">'
            '{}</span>', color, obj.status
        )

    @admin.display(description="Progress", ordering='total_curr')
    def completion_progress(self, obj):
        total_req = getattr(obj, 'total_req', 0) or 0
        total_curr = getattr(obj, 'total_curr', 0) or 0
        
        progress = 0
        if total_req > 0:
            progress = int((total_curr / total_req) * 100)
            progress = min(progress, 100)
            
        color = "#10b981" if progress == 100 else "#3b82f6"
        
        return format_html(
            '<div style="width: 100px; background: #e2e8f0; border-radius: 4px; height: 8px; overflow: hidden; margin-bottom: 4px;">'
            '  <div style="width: {}%; background: {}; height: 100%; transition: width 0.3s;"></div>'
            '</div>'
            '<span style="font-size: 11px; font-weight: 700; color: #64748b;">{}% Complete</span>',
            progress, color, progress
        )

    @admin.display(description="Stats")
    def stats_summary(self, obj):
        docs = getattr(obj, 'doc_count', 0)
        workers = getattr(obj, 'worker_count', 0)
        annots = getattr(obj, 'annot_count', 0)
        return format_html(
            '<div style="display: flex; gap: 8px; font-size: 11px; font-weight: 600;">'
            '  <span title="Documents" style="color: #3b82f6;">📄 {}</span>'
            '  <span title="Annotations" style="color: #10b981;">📝 {}</span>'
            '  <span title="Workers" style="color: #8b5cf6;">👥 {}</span>'
            '</div>',
            docs, annots, workers
        )

    def get_queryset(self, request):
        from django.db.models import Sum, Count, Q
        qs = super().get_queryset(request)
        qs = qs.annotate(
            total_req=Sum('documents__min_annotations_required', filter=Q(documents__is_gold_unit=False)),
            total_curr=Sum('documents__current_annotations_count', filter=Q(documents__is_gold_unit=False)),
            doc_count=Count('documents', filter=Q(documents__is_gold_unit=False), distinct=True),
            worker_count=Count('enrollments', distinct=True),
            annot_count=Count('documents__annotations', distinct=True)
        )
        return qs

    @admin.display(description="Management")
    def manage_project_link(self, obj):
        url = reverse('admin:project_dashboard', args=[obj.slug])
        return format_html(
            '<a href="{}" class="bg-primary-600 text-white px-3 py-1 rounded-md text-xs font-bold hover:bg-primary-700 transition inline-block">'
            '📊 DASHBOARD</a>', 
            url
        )

    actions = []
    form = ProjectAdminForm
    readonly_fields = (
        'status_notice',
        'status_badge',
        'formatted_annotation_schema',
        'formatted_screening_config',
        'formatted_codebook_content',
        'formatted_instructions_content',
        'formatted_practice_task_config',
        'formatted_informed_consent_content',
    )
    
    tabs = [
        ("details", "Project Details"),
        ("config", "Task Configuration"),
        ("training", "Training & Instructions"),
        ("quality", "Quality / Monitoring"),
        ("distribution", "Distribution & Launch"),
        ("log", "Activity Log"),
    ]

    inlines = [ProjectLogInline]

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj and (obj.is_published or obj.status == 'LIVE'):
            locked = ['name', 'slug', 'description', 'informed_consent_config', 'dataset_text_key', 'dataset_id_key', 'enable_screening', 'enable_codebook', 'enable_instructions', 'enable_practice_task', 'practice_task_required', 'enable_gold_units', 'gold_injection_frequency', 'min_accuracy_required', 'min_gold_before_eval', 'distribution_strategy', 'min_annotations_per_doc', 'max_annotations_per_doc', 'block_size', 'annotators_per_block', 'prioritize_unannotated', 'documents_file', 'gold_units_file', 'prolific_completion_code']
            for f in locked:
                if f not in readonly: readonly.append(f)
        return readonly

    def get_fieldsets(self, request, obj=None):
        """Dynamically inject status notice into all tab descriptions."""
        notice_html = ""
        if obj:
            if obj.is_published:
                clone_url = reverse('admin:project_quick_clone', args=[obj.pk])
                notice_html = format_html(
                    '''
                    <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 16px; border-radius: 4px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px;">
                        <div style="line-height: 1.5;">
                            <b style="color: #f59e0b; font-size: 1.1em;">🔒 Official Project & Locked</b><br>
                            <span style="color: #94a3b8;">This configuration is sealed to ensure data integrity. To make structural changes, you must clone the project.</span>
                        </div>
                        <button type="button" onclick="quickCloneProject(this, '{}', '{}', true)" style="background: #f59e0b; color: white; padding: 8px 16px; border-radius: 6px; font-weight: 800; border:none; cursor:pointer; font-size: 12px;">📋 CLONE PROJECT</button>
                    </div>
                    ''',
                    clone_url, obj.name
                )
            elif obj.status == 'LIVE':
                draft_url = reverse('admin:project_set_status', args=[obj.pk])
                notice_html = format_html(
                    '''
                    <div style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px;">
                        <div style="line-height: 1.5;">
                            <b style="color: #60a5fa; font-size: 1.1em;">▶️ Playground Active (LIVE)</b><br>
                            <span style="color: #94a3b8;">The project is read-only during testing/simulation. Return to Draft to unlock all fields.</span>
                        </div>
                        <button type="button" onclick="quickUpdateStatus(this, '{}', 'DRAFT', 'Draft')" style="background: #3b82f6; color: white; padding: 8px 16px; border-radius: 6px; font-weight: 800; border:none; cursor:pointer; font-size: 12px;">📁 RETURN TO DRAFT</button>
                    </div>
                    ''',
                    draft_url
                )

        # Standard fieldsets but with notice_html prepended to descriptions
        return (
            ("Project Details", {
                "fields": (("name", "slug"), "description",),
                "classes": ("tab", "details"),
                "description": mark_safe(f"{notice_html}<div style='display:flex; gap:10px; margin-top:20px;'>\
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #3B82F6; color:#ddd; border-radius:4px;'>\
                        <b style='color:#60a5fa; font-size:1.1em;'>📝 Project Details</b><br>In this section you can edit the project name, slug (URL), and description.\
                    </div>\
                </div>")
                }),
            ("Dataset Upload", {
                "classes": ("tab", "config"),
                "fields": (
                    "documents_file",
                    ("dataset_text_key", "dataset_id_key"),
                ),
                "description": mark_safe(f"""{notice_html}
                <div style='display:flex; gap:10px; margin-top:20px; margin-bottom: 20px;'>
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #10b981; color:#ddd; border-radius:4px;'>
                        <b style='color:#10b981; font-size:1.1em;'>📁 Dataset Upload</b><br>
                        Upload your source data (JSONL) and specify which fields contain the text to annotate and the unique ID.
                    </div>
                </div>""")
            }),
            ("Annotation Schema", {
                "classes": ("tab", "config"),
                "fields": (
                    "formatted_annotation_schema",
                    "upload_task_config",
                ),
                "description": mark_safe(f"""{notice_html}
                <div style='display:flex; gap:10px; margin-top:20px; margin-bottom: 20px;'>
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #60a5fa; color:#ddd; border-radius:4px;'>
                        <b style='color:#60a5fa; font-size:1.1em;'>⚙️ Task Configuration</b><br>
                        Define the core logic of your annotation task. Upload the configuration JSON or edit the schema directly to set up labels and instructions.
                    </div>
                </div>

                <style>
                .schema-docs summary {{
                    list-style: none;
                    cursor: pointer;
                    user-select: none;
                }}
                .schema-docs summary::-webkit-details-marker {{ display: none; }}
                .schema-docs[open] .schema-docs-arrow {{ transform: rotate(90deg); }}
                .schema-docs-arrow {{
                    display: inline-block;
                    transition: transform 0.2s ease;
                    font-style: normal;
                    margin-right: 6px;
                }}
                </style>

                <details class="schema-docs" style="margin-top:16px;">
                <summary>
                    <div style="display:inline-flex; align-items:center; gap:8px; background:#1e293b;
                                padding:10px 16px; border-left:4px solid #3B82F6; border-radius:4px;
                                font-size:13px; color:#94a3b8; font-weight:500;">
                    <i class="schema-docs-arrow">▶</i>
                    <span style="color:#60a5fa;">⚙️ Annotation Schema Documentation</span>
                    <span style="color:#475569; font-weight:400; font-size:12px;">— click to view configuration reference</span>
                    </div>
                </summary>

                <div style='margin-top:10px; display:flex; flex-direction:column; gap:12px; font-size:13px; color:#cbd5e1;'>

                    <!-- Overview -->
                    <div style='background:#1e293b; padding:14px 18px; border-left:4px solid #3B82F6; border-radius:4px;'>
                    Upload a <code style='background:#0f172a; padding:1px 6px; border-radius:3px; color:#93c5fd;'>.yaml</code> file
                    that defines how annotators interact with each document.
                    The schema drives both the live annotation view and the practice task.
                    </div>

                    <!-- components[] -->
                    <div style='background:#1e293b; padding:14px 18px; border-left:4px solid #8B5CF6; border-radius:4px;'>
                    <b style='color:#a78bfa;'>components <span style="font-weight:400; color:#94a3b8;">(list, required)</span></b><br>
                    Ordered list of annotation modules rendered to the annotator. Supported types:
                    <table style='margin-top:8px; border-collapse:collapse; width:100%;'>
                        <tr style='border-bottom:1px solid #334155;'>
                        <td style='padding:4px 10px 4px 0; color:#7dd3fc; white-space:nowrap;'><code>span_highlight</code></td>
                        <td style='padding:4px 0; color:#94a3b8;'>Interactive text highlighter. Requires <code>labels[]</code>.</td>
                        </tr>
                        <tr>
                        <td style='padding:4px 10px 4px 0; color:#7dd3fc; white-space:nowrap;'><code>classification</code></td>
                        <td style='padding:4px 0; color:#94a3b8;'>Radio / checkbox buttons. Requires <code>options[]</code>.</td>
                        </tr>
                    </table>
                    <div style='margin-top:10px; display:flex; gap:10px; flex-wrap:wrap;'>
                        <div style='background:#0f172a; padding:8px 12px; border-radius:4px; border:1px solid #334155;'>
                        <div style='color:#64748b; font-size:11px; margin-bottom:4px;'>HYBRID (default)</div>
                        <pre style='margin:0; color:#e2e8f0; font-size:11px;'>components:
  - type: span_highlight
    labels: [...]
  - type: classification
    options: [...]</pre>
                        </div>
                        <div style='background:#0f172a; padding:8px 12px; border-radius:4px; border:1px solid #334155;'>
                        <div style='color:#64748b; font-size:11px; margin-bottom:4px;'>CLASSIFICATION ONLY</div>
                        <pre style='margin:0; color:#e2e8f0; font-size:11px;'>components:
  - type: classification
    options: [...]</pre>
                        </div>
                        <div style='background:#0f172a; padding:8px 12px; border-radius:4px; border:1px solid #334155;'>
                        <div style='color:#64748b; font-size:11px; margin-bottom:4px;'>SPAN ONLY</div>
                        <pre style='margin:0; color:#e2e8f0; font-size:11px;'>components:
  - type: span_highlight
    labels: [...]</pre>
                        </div>
                    </div>
                    </div>

                    <!-- span_highlight fields -->
                    <div style='background:#1e293b; padding:14px 18px; border-left:4px solid #10B981; border-radius:4px;'>
                    <b style='color:#34d399;'>span_highlight.labels <span style="font-weight:400; color:#94a3b8;">(list, required)</span></b><br>
                    Each entry defines one highlight category:
                    <table style='margin-top:8px; border-collapse:collapse; width:100%;'>
                        <tr style='border-bottom:1px solid #334155;'>
                        <td style='padding:3px 10px 3px 0; color:#7dd3fc;'><code>name</code></td><td style='color:#94a3b8;'>Label identifier — appears in the result payload</td>
                        </tr>
                        <tr style='border-bottom:1px solid #334155;'>
                        <td style='padding:3px 10px 3px 0; color:#7dd3fc;'><code>color</code></td><td style='color:#94a3b8;'>Hex colour for the highlight badge (e.g. <code>"#FF5733"</code>)</td>
                        </tr>
                        <tr>
                        <td style='padding:3px 10px 3px 0; color:#7dd3fc;'><code>hover_hint</code></td><td style='color:#94a3b8;'>Tooltip shown on the label button <span style='color:#64748b;'>(optional)</span></td>
                        </tr>
                    </table>
                    </div>

                    <!-- classification fields -->
                    <div style='background:#1e293b; padding:14px 18px; border-left:4px solid #F59E0B; border-radius:4px;'>
                    <b style='color:#fbbf24;'>classification.options <span style="font-weight:400; color:#94a3b8;">(list, required)</span></b><br>
                    Each entry is one answer option:
                    <table style='margin-top:8px; border-collapse:collapse; width:100%;'>
                        <tr style='border-bottom:1px solid #334155;'>
                        <td style='padding:3px 10px 3px 0; color:#7dd3fc;'><code>label</code></td><td style='color:#94a3b8;'>Display text shown to the annotator</td>
                        </tr>
                        <tr style='border-bottom:1px solid #334155;'>
                        <td style='padding:3px 10px 3px 0; color:#7dd3fc;'><code>value</code></td><td style='color:#94a3b8;'>Machine-readable value stored in the result</td>
                        </tr>
                        <tr>
                        <td style='padding:3px 10px 3px 0; color:#7dd3fc;'><code>hover_hint</code></td><td style='color:#94a3b8;'>Tooltip for this option <span style='color:#64748b;'>(optional)</span></td>
                        </tr>
                    </table>
                    Optional component-level fields:
                    <code style='background:#0f172a; padding:1px 5px; border-radius:3px; color:#fbbf24;'>question</code> (string) ·
                    <code style='background:#0f172a; padding:1px 5px; border-radius:3px; color:#fbbf24;'>multi_select</code> (bool, default false)
                    </div>

                    <!-- Result payload -->
                    <div style='background:#1e293b; padding:14px 18px; border-left:4px solid #EC4899; border-radius:4px;'>
                    <b style='color:#f472b6;'>Result payload stored per annotation</b><br>
                    <pre style='margin:8px 0 0; color:#e2e8f0; font-size:11px; background:#0f172a; padding:10px; border-radius:4px;'>{{{{
  "span_highlight": [{{{{"start": 12, "end": 28, "label": "Actor"}}}}],
  "classification": "Yes"
}}}}</pre>
                    </div>

                </div>
                </details>""")
            }),

            ("Screening Setup", {
                "classes": ("tab", "training"),
                "fields": (
                    "enable_screening",
                    "formatted_screening_config",
                    "upload_screening_config",
                ),
                "description": mark_safe(f"{notice_html}<div style='display:flex; gap:10px; margin-top:20px;'>\
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #10B981; color:#ddd; border-radius:4px;'>\
                        <b style='color:#10B981; font-size:1.1em;'>📋 Screening Setup</b><br>Configure the screening questionnaire (demographics, eligibility criteria, etc.) shown to participants before they begin annotation. Toggle on/off as needed.\
                    </div>\
                </div>")
            }),
            ("Codebook Setup", {
                "classes": ("tab", "training"),
                "fields": (
                    "enable_codebook",
                    "formatted_codebook_content",
                    "upload_codebook_content",
                ),
                "description": mark_safe(f"{notice_html}<div style='display:flex; gap:10px; margin-top:20px;'>\
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #8B5CF6; color:#ddd; border-radius:4px;'>\
                        <b style='color:#a78bfa; font-size:1.1em;'>📖 Codebook Setup</b><br>Upload a Codebook (Markdown) to define the theoretical and practical guidelines annotators should follow. Toggle on/off as needed.\
                    </div>\
                </div>")
            }),
            ("Instructions", {
                "classes": ("tab", "training"),
                "fields": (
                    "enable_instructions",
                    "formatted_instructions_content",
                    "upload_instructions_content",
                ),
                "description": mark_safe(f"{notice_html}<div style='display:flex; gap:10px; margin-top:20px;'>\
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #F59E0B; color:#ddd; border-radius:4px;'>\
                        <b style='color:#f59e0b; font-size:1.1em;'>📝 Instructions</b><br>Upload a Markdown file with detailed task instructions shown to annotators before they start working. Toggle on/off as needed.\
                    </div>\
                </div>")
            }),
            ("Practice Task", {
                "classes": ("tab", "training"),
                "fields": (
                    "enable_practice_task",
                    "formatted_practice_task_config",
                    "upload_practice_task_config",
                    "practice_task_required",
                ),
                "description": mark_safe(f"{notice_html}<div style='display:flex; gap:10px; margin-top:20px;'>\
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #EC4899; color:#ddd; border-radius:4px;'>\
                        <b style='color:#f472b6; font-size:1.1em;'>🎯 Practice Task</b><br>Set up a training exercise with gold-standard examples so annotators can practice before the real task. Toggle on/off and mark as required if needed.\
                    </div>\
                </div>")
            }),
            ("Quality & Monitoring", {
                "classes": ("tab", "quality"),
                "fields": (
                    "enable_gold_units",
                    "gold_injection_frequency",
                    ("min_accuracy_required", "min_gold_before_eval"),
                    "gold_units_file",
                ),
                "description": mark_safe(f"{notice_html}<div style='display:flex; gap:10px; margin-top:20px;'>\
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #8B5CF6; color:#ddd; border-radius:4px;'>\
                        <b style='color:#a78bfa; font-size:1.1em;'>🛡️ Monitoring & Quality</b><br>Monitor data quality using Gold Units and accuracy thresholds. Use the <b>Actions</b> menu to run <b>MACE Analysis</b> to calculate annotator reliability.\
                    </div>\
                </div>")
            }),
            ("Distribution", {
                "classes": ("tab", "distribution"),
                "fields": (
                    "prolific_completion_code",
                    "distribution_strategy",
                    ("min_annotations_per_doc", "max_annotations_per_doc"),
                    ("block_size", "annotators_per_block"),
                    "prioritize_unannotated",
                    "formatted_informed_consent_content",
                    "upload_informed_consent_content",
                ),
                "description": mark_safe(f"{notice_html}<div style='display:flex; gap:10px; margin-top:20px;'>\
                    <div style='flex:1; background:#2a2a2a; padding:15px; border-left:4px solid #3B82F6; color:#ddd; border-radius:4px;'>\
                        <b style='color:#3b82f6; font-size:1.1em;'>🚀 Distribution Criteria</b><br>Define how documents are assigned (Distribution Strategies) and configure Prolific completion codes. Manage the <b>Informed Consent</b> text (Markdown) shown to participants before the task. When ready, use the <b>Launch</b> button to publish.\
                    </div>\
                </div>")
            }),
        )

    class Media:
        css = {
            'all': ('css/admin_project.css',)
        }
        js = ('js/admin_project.js',)

    def _colorize_yaml(self, yaml_str):
        """
        Syntax-highlight a YAML string for HTML display.

        Approach: classify each line into one exclusive category so that
        no regex can accidentally re-match HTML we already injected.

        Categories (checked in order):
          1. Comment line         →  gray italic
          2. Bullet + scalar      →  bullet muted, value white
          3. Bullet + key: val    →  bullet muted, key sky, value coloured
          4. Key: val / Key:      →  key sky, value coloured
          5. Fallback             →  unchanged
        """
        from django.utils.html import escape

        # ── Colour palette (matches admin_project.css classes) ──────────────
        C_KEY     = 'class="json-key"'          # #7dd3fc sky-300
        C_STRING  = 'class="json-string"'        # #86efac green-300
        C_NUMBER  = 'class="json-number"'        # #fbbf24 amber-400
        C_BOOL    = 'class="json-bool"'          # #c084fc purple-400
        C_VALUE   = 'style="color:#e2e8f0;"'     # slate-200 – unquoted scalars
        C_BULLET  = 'style="color:#94a3b8;"'     # slate-400
        C_COMMENT = 'style="color:#64748b; font-style:italic;"'

        def _val(raw):
            """Return a coloured <span> for the value part after ':'."""
            s = raw.strip()
            if not s:
                return raw  # key-only line → keep trailing newline as-is
            # Single-quoted YAML string  → 'value'  (not HTML-escaped by Django)
            if re.match(r"^'[^']*'$", s):
                return f' <span {C_STRING}>{s}</span>'
            # Double-quoted string (Django escapes " to &quot;)
            if re.match(r'^&quot;.*&quot;$', s):
                return f' <span {C_STRING}>{s}</span>'
            # Integer or float
            if re.match(r'^\-?\d+\.?\d*$', s):
                return f' <span {C_NUMBER}>{s}</span>'
            # Boolean / null (YAML accepts multiple casings)
            if re.match(r'^(true|false|null|yes|no|True|False|Null|Yes|No)$', s):
                return f' <span {C_BOOL}>{s}</span>'
            # Unquoted scalar
            return f' <span {C_VALUE}>{s}</span>'

        escaped = escape(yaml_str)
        lines = escaped.split('\n')
        result = []

        for line in lines:

            # 1. Comment lines ───────────────────────────────────────────────
            if re.match(r'^\s*#', line):
                result.append(f'<span {C_COMMENT}>{line}</span>')
                continue

            # 2. Bullet + bare scalar  "  - Actor"  (no colon in scalar part)
            m = re.match(r'^(\s*)(- )(\S.*)$', line)
            if m and ':' not in m.group(3):
                indent, scalar = m.group(1), m.group(3)
                result.append(
                    f'{indent}'
                    f'<span {C_BULLET}>- </span>'
                    f'<span {C_VALUE}>{scalar}</span>'
                )
                continue

            # 3. Bullet + key: [value]  "  - name: Actor"
            m = re.match(r'^(\s*)(- )([^\s:][^:]*?)(:)([ \t].*|)$', line)
            if m:
                indent, key, value_part = m.group(1), m.group(3), m.group(5)
                result.append(
                    f'{indent}'
                    f'<span {C_BULLET}>- </span>'
                    f'<span {C_KEY}>{key}</span>'
                    f':{_val(value_part)}'
                )
                continue

            # 4. Regular key: [value]  "  name: Actor"  or  "name:"
            m = re.match(r'^(\s*)([^\s#:][^:]*?)(:)([ \t].*|)$', line)
            if m:
                indent, key, value_part = m.group(1), m.group(2), m.group(4)
                result.append(
                    f'{indent}'
                    f'<span {C_KEY}>{key}</span>'
                    f':{_val(value_part)}'
                )
                continue

            # 5. Fallback ────────────────────────────────────────────────────
            result.append(line)

        return '\n'.join(result)


    def _render_config_block(self, obj, config_data, title, icon):
        """Render a structured config (dict/list) as a YAML-formatted HTML block."""
        if not config_data:
            return format_html(
                '<div class="config-empty">'
                '<span class="empty-icon">{}</span>'
                '<span>No {} configured yet. Upload a YAML file above.</span>'
                '</div>',
                icon, title.lower()
            )

        # Ensure important keys are on top if it's a dictionary
        if isinstance(config_data, dict):
            priority_keys = ["min_accuracy_required", "gold_injection_frequency", "continuous_exclusion"]
            ordered_data = {k: config_data[k] for k in priority_keys if k in config_data}
            for k, v in config_data.items():
                if k not in ordered_data:
                    ordered_data[k] = v
            config_data = ordered_data

        yaml_str = yaml.dump(config_data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        colorized = self._colorize_yaml(yaml_str)

        return format_html(
            '<div class="json-config-display break-words max-w-none py-3 text-sm bg-base-50 border border-base-200 font-medium px-4 rounded-default shadow-xs dark:border-base-700 dark:bg-base-800">'
            '  <div class="config-header" style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(128,128,128,0.1); color: #64748b;">'
            '    <div style="display: flex; align-items: center; gap: 8px;">'
            '      <span class="config-icon">{icon}</span> <strong style="font-size: 13px;">{title}</strong>'
            '    </div>'
            '    <div style="display: flex; gap: 6px;">'
            '        <button type="button" class="copy-json-btn" onclick="copyConfigToClipboard(this)" '
            '                style="background: rgba(48,110,232,0.1); color: #306ee8; border: none; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.2s;"'
            '                onmouseover="this.style.background=\'rgba(48,110,232,0.2)\'" onmouseout="this.style.background=\'rgba(48,110,232,0.1)\'">'
            '           📋 Copy YAML'
            '        </button>'
            '    </div>'
            '  </div>'
            '  <div class="json-raw-content" style="display: none;">{raw_yaml}</div>'
            '  <pre style="font-family: \'JetBrains Mono\', monospace; font-size: 13px; line-height: 1.5; color: inherit; white-space: pre-wrap; margin: 0;">{colorized}</pre>'
            '</div>',
            icon=icon,
            title=title,
            raw_yaml=yaml_str,
            colorized=mark_safe(colorized)
        )

    @admin.display(description="")
    def status_notice(self, obj):
        if not obj or not obj.pk:
            return ""
            
        if obj.is_published:
            clone_url = reverse('admin:project_quick_clone', args=[obj.pk])
            return format_html(
                '''
                <div style="background: rgba(245, 158, 11, 0.15); border: 2px solid #f59e0b; border-radius: 12px; padding: 20px; margin-bottom: 5px; display: flex; align-items: center; justify-content: space-between; gap: 16px; width: 100%;">
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <span style="font-size: 32px;">🔒</span>
                        <div style="line-height: 1.5;">
                            <div style="font-weight: 900; color: #f59e0b; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px;">Project Launched & Locked</div>
                            <div style="color: #94a3b8; font-size: 13.5px; font-weight: 500;">Configuration is sealed to ensure scientific validity. To modify parameters, you must create a copy.</div>
                        </div>
                    </div>
                    <button type="button" onclick="quickCloneProject(this, '{}', '{}', true)" style="background: #f59e0b; color: white; padding: 10px 20px; border-radius: 10px; font-weight: 800; border:none; cursor:pointer; font-size: 13px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); transition: transform 0.1s;" onmousedown="this.style.transform='scale(0.95)'" onmouseup="this.style.transform='scale(1)'">📋 CLONE & EDIT</button>
                </div>
                ''',
                clone_url, obj.name
            )
        elif obj.status == 'LIVE':
            draft_url = reverse('admin:project_set_status', args=[obj.pk])
            return format_html(
                '''
                <div style="background: rgba(59, 130, 246, 0.15); border: 2px solid #3b82f6; border-radius: 12px; padding: 20px; margin-bottom: 5px; display: flex; align-items: center; justify-content: space-between; gap: 16px; width: 100%;">
                    <div style="display: flex; gap: 15px; align-items: center;">
                        <span style="font-size: 32px;">▶️</span>
                        <div style="line-height: 1.5;">
                            <div style="font-weight: 900; color: #3b82f6; font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px;">Playground Active (LIVE)</div>
                            <div style="color: #94a3b8; font-size: 13.5px; font-weight: 500;">The project is in testing phase. Fields are read-only to prevent conflicts; return to DRAFT to make changes.</div>
                        </div>
                    </div>
                    <button type="button" onclick="quickUpdateStatus(this, '{}', 'DRAFT', 'Draft')" style="background: #3b82f6; color: white; padding: 10px 20px; border-radius: 10px; font-weight: 800; border:none; cursor:pointer; font-size: 13px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); transition: transform 0.1s;" onmousedown="this.style.transform='scale(0.95)'" onmouseup="this.style.transform='scale(1)'">📁 RETURN TO DRAFT</button>
                </div>
                ''',
                draft_url
            )
        return ""

    @admin.display(description="Annotation Schema")
    def formatted_annotation_schema(self, obj):
        return self._render_config_block(obj, obj.annotation_schema, 'Annotation Schema', '⚙️')

    @admin.display(description="Screening Config")
    def formatted_screening_config(self, obj):
        return self._render_config_block(obj, obj.screening_config, 'Screening Configuration', '📋')

    def _render_markdown_block(self, obj, md_text, title, icon):
        """Convert Markdown text to styled HTML for admin display."""
        from django.utils.html import escape
        
        if not md_text or not md_text.strip():
            return format_html(
                '<div class="config-empty">'
                '<span class="empty-icon">{}</span>'
                '<span>No {} configured yet. Upload a Markdown file above.</span>'
                '</div>',
                icon, title.lower()
            )

        text = escape(md_text)

        # Headers
        text = re.sub(r'^### (.+)$', r'<h4 style="font-size:14px;font-weight:600;color:#64748b;margin:16px 0 6px;">\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h3 style="font-size:16px;font-weight:600;color:#306ee8;margin:20px 0 8px;">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h2 style="font-size:18px;font-weight:700;color:inherit;margin:24px 0 10px;padding-bottom:6px;border-bottom:1px solid rgba(128,128,128,0.2);">\1</h2>', text, flags=re.MULTILINE)

        # Bold + italic
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic with underscores (_text_) and asterisks (*text*)
        text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', text)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)

        # Inline code
        text = re.sub(r'`(.+?)`', r'<code style="background:rgba(128,128,128,0.15);padding:1px 5px;border-radius:3px;font-size:0.9em;">\1</code>', text)

        # Blockquotes
        text = re.sub(
            r'^&gt; (.+)$',
            r'<div style="border-left:3px solid #306ee8;padding:6px 12px;margin:8px 0;background:rgba(48,110,232,0.06);border-radius:0 6px 6px 0;font-size:0.92em;">\1</div>',
            text, flags=re.MULTILINE
        )

        # Horizontal rules
        text = re.sub(r'^---$', r'<hr style="border:none;border-top:1px solid rgba(128,128,128,0.2);margin:20px 0;">', text, flags=re.MULTILINE)

        # Unordered list items (handle nested with 2+ spaces)
        text = re.sub(
            r'^  - (.+)$',
            r'<div style="padding-left:28px;margin:3px 0;"><span style="color:#306ee8;margin-right:6px;">◦</span>\1</div>',
            text, flags=re.MULTILINE
        )
        text = re.sub(
            r'^- (.+)$',
            r'<div style="padding-left:8px;margin:4px 0;"><span style="color:#306ee8;margin-right:6px;">•</span>\1</div>',
            text, flags=re.MULTILINE
        )

        # Paragraphs — wrap remaining non-tag lines
        processed = []
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('<'):
                processed.append(f'<p style="margin:6px 0;line-height:1.7;">{stripped}</p>')
            else:
                processed.append(line)
        text = '\n'.join(processed)

        # Remove empty paragraphs
        text = re.sub(r'<p[^>]*>\s*</p>', '', text)

        return format_html(
            '<div class="json-config-display break-words max-w-none py-3 text-sm bg-base-50 border border-base-200 font-medium px-4 rounded-default shadow-xs dark:border-base-700 dark:bg-base-800">'
            '  <div class="config-header" style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid rgba(128,128,128,0.1); color: #64748b;">'
            '    <div style="display: flex; align-items: center; gap: 8px;">'
            '      <span class="config-icon">{icon}</span> <strong style="font-size: 13px;">{title}</strong>'
            '    </div>'
            '    <div style="display: flex; gap: 6px;">'
            '        <button type="button" class="copy-json-btn" onclick="copyMarkdownToClipboard(this)" '
            '                style="background: rgba(48,110,232,0.1); color: #306ee8; border: none; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.2s;"'
            '                onmouseover="this.style.background=\'rgba(48,110,232,0.2)\'" onmouseout="this.style.background=\'rgba(48,110,232,0.1)\'">'
            '           📋 Copy Markdown'
            '        </button>'
            '    </div>'
            '  </div>'
            '  <div class="markdown-raw-content" style="display: none;">{raw_md}</div>'
            '  <div style="font-family: \'Outfit\', \'Inter\', sans-serif; font-size: 13px; line-height: 1.7; color: inherit;">{content}</div>'
            '</div>',
            icon=icon,
            title=title,
            content=mark_safe(text),
            raw_md=md_text
        )

    @admin.display(description="Codebook Content")
    def formatted_codebook_content(self, obj):
        return self._render_markdown_block(obj, obj.codebook_content, 'Codebook Materials', '📖')

    @admin.display(description="Instructions Content")
    def formatted_instructions_content(self, obj):
        return self._render_markdown_block(obj, obj.instructions_content, 'Task Instructions', '📝')

    @admin.display(description="Informed Consent Content")
    def formatted_informed_consent_content(self, obj):
        return self._render_markdown_block(obj, obj.informed_consent_config, 'Informed Consent', '📜')

    @admin.display(description="Practice Task Config")
    def formatted_practice_task_config(self, obj):
        return self._render_config_block(obj, obj.practice_task_config, 'Practice Task', '🎯')

    def dashboard_view(self, request, slug):
        project = get_object_or_404(Project, slug=slug)
        
        # Gather stats
        # A worker is considered 'test' if is_test is True OR if metadata has {"is_test": "true"}
        test_q = Q(annotator__is_test=True) | Q(annotator__metadata__is_test="true")
        
        stats = {
             'docs': project.documents.filter(is_gold_unit=False).count(),
             'gold': project.documents.filter(is_gold_unit=True).count(),
             'enrollments': project.enrollments.exclude(test_q).count(),
             'test_enrollments': project.enrollments.filter(test_q).count(),
             'annotations': Annotation.objects.filter(document__project=project, is_test=False).count(),
             'test_annotations': Annotation.objects.filter(document__project=project, is_test=True).count(),
        }
        
        # Progress calculation: Volume-based for better granularity
        regular_docs = project.documents.filter(is_gold_unit=False)
        total_req_annotations = regular_docs.aggregate(total=Sum('min_annotations_required'))['total'] or 0
        total_curr_annotations = regular_docs.aggregate(total=Sum('current_annotations_count'))['total'] or 0
        
        if total_req_annotations > 0:
            # We use the total volume of annotations to provide a smoother progress bar
            progress = int((total_curr_annotations / total_req_annotations) * 100)
            if progress > 100: progress = 100
        else:
            progress = 0

        p_completed = regular_docs.filter(current_annotations_count__gte=F('min_annotations_required')).count()
        
        # Action URLs
        action_urls = {
            'export': reverse('admin:project_export_jsonl', args=[project.pk]),
            'set_status': reverse('admin:project_set_status', args=[project.pk]),
            'nuke': reverse('admin:project_nuke_data', args=[project.pk]),
            'launch': reverse('admin:project_launch_data', args=[project.pk]),
            'clone': reverse('admin:project_quick_clone', args=[project.pk]),
            'run_mace': reverse('admin:project_run_mace', args=[project.pk]),
            'settings': reverse('admin:annotation_project_change', args=[project.pk]),
            'dashboard': reverse('admin:project_dashboard', args=[project.slug]),
        }
        
        # For simple list of status transitions
        status_transitions = []
        for val, label in Project.STATUS_CHOICES:
            if val == project.status: continue
            if project.is_published and val == 'DRAFT': continue
            status_transitions.append({'value': val, 'label': label})

        context = {
            **self.admin_site.each_context(request),
            'project': project,
            'stats': stats,
            'progress': progress,
            'action_urls': action_urls,
            'status_transitions': status_transitions,
            'logs': project.logs.all()[:10],
            'opts': self.model._meta,
            'title': f"Dashboard: {project.name}",
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/'),
        }
        return render(request, 'admin/annotation/project/dashboard.html', context)

    def get_urls(self):
        urls = super(ProjectAdmin, self).get_urls()
        my_urls = [
            path(
                '<slug:slug>/dashboard/', 
                self.admin_site.admin_view(self.dashboard_view), 
                name='project_dashboard'
            ),
            path(
                '<path:object_id>/export/', 
                self.admin_site.admin_view(self.download_export_view), 
                name='project_export_jsonl'
            ),
            path(
                '<path:object_id>/set-status/',
                self.admin_site.admin_view(self.set_status_view),
                name='project_set_status'
            ),
            path(
                '<path:object_id>/nuke-data/',
                self.admin_site.admin_view(self.nuke_project_view),
                name='project_nuke_data'
            ),
            path(
                '<path:object_id>/launch-data/',
                self.admin_site.admin_view(self.launch_project_view),
                name='project_launch_data'
            ),
            path(
                '<path:object_id>/quick-clone/',
                self.admin_site.admin_view(self.clone_project_view),
                name='project_quick_clone'
            ),
            path(
                '<path:object_id>/run-mace/',
                self.admin_site.admin_view(self.run_mace_view),
                name='project_run_mace'
            ),
        ]
        return my_urls + urls

    def set_status_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            project, message = ProjectService.set_project_status(object_id, new_status, user=request.user)
            return JsonResponse({'status': 'success', 'new_status': project.status, 'message': message})
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') and len(e.messages) > 0 else str(e)
            return JsonResponse({'status': 'error', 'message': str(msg)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def nuke_project_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
        try:
            message = ProjectService.nuke_project_data(object_id, user=request.user)
            return JsonResponse({'status': 'success', 'message': message})
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def launch_project_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
        try:
            message = ProjectService.launch_project(object_id, user=request.user)
            return JsonResponse({'status': 'success', 'message': message})
        except ValidationError as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            return JsonResponse({'status': 'error', 'message': str(msg)}, status=400)
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def clone_project_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
        try:
            data = json.loads(request.body)
            clone_mode = data.get('clone_mode')
            new_name = data.get('new_name')
            if not clone_mode:
                clone_dataset = data.get('clone_dataset', False)
                clone_mode = 'full' if clone_dataset else 'config'
            
            project, message = ProjectService.clone_project(
                object_id, 
                clone_mode=clone_mode, 
                user=request.user,
                new_name=new_name
            )
            return JsonResponse({'status': 'success', 'message': message})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def run_mace_view(self, request, object_id):
        if request.method != 'POST':
            return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)
        
        try:
            result = run_mace_for_project(object_id)
            if result.get("status") == "success":
                return JsonResponse({'status': 'success', 'message': result['message']})
            else:
                return JsonResponse({'status': 'error', 'message': result.get('message', 'MACE Error')}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def download_export_view(self, request, object_id):
        project = self.get_object(request, object_id)
        response = HttpResponse(content_type='application/x-jsonlines')
        filename = f"{project.name.replace(' ', '_').lower()}_annotations.jsonl"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        annotations = Annotation.objects.filter(
            document__project=project,
            document__is_gold_unit=False,
            is_test=False
        ).select_related('document', 'annotator')

        for ann in annotations:
            raw_result = ann.result
            formatted_markers = []
            raw_spans = raw_result.get('spans') or raw_result.get('span_highlight') or []
            if isinstance(raw_spans, list):
                for span in raw_spans:
                    formatted_markers.append({
                        "startIndex": span.get('start'),
                        "endIndex": span.get('end'),
                        "type": span.get('label'),
                        "text": span.get('text')
                    })

            output_obj = {
                "_id": ann.document.external_id,
                "conspiracy": raw_result.get('classification'),
                "markers": formatted_markers,
                "subreddit": ann.document.metadata.get('subreddit', 'unknown'),
                "annotator": ann.annotator.prolific_pid
            }
            response.write(json.dumps(output_obj) + '\n')
        return response

    @admin.display(description="Export")
    def export_list_button(self, obj):
        url = reverse('admin:project_export_jsonl', args=[obj.pk])
        return format_html(
            '''
            <button type="button" 
               onclick="quickExportProject(this, '{}', '{}')"
               class="bg-primary-600 text-white px-2 py-1 rounded text-xs font-bold hover:bg-primary-700 transition inline-block whitespace-nowrap text-center cursor-pointer border-none"
               title="Download .jsonl">
               ⬇ JSONL
            </button>
            ''',
            url, obj.name
        )

    @admin.display(description="Status & Operations", ordering='status')
    def status_badge(self, obj):
        status_colors = {
            'DRAFT': ('#64748b', '📁'), 
            'LIVE': ('#10b981', '▶️'),   
            'PAUSED': ('#f59e0b', '⏸️'), 
            'COMPLETED': ('#3b82f6', '✅'), 
        }
        bg_color, icon = status_colors.get(obj.status, ('#64748b', '❓'))
        buttons_html = ""
        for val, label in Project.STATUS_CHOICES:
            if val == obj.status: continue
            if obj.is_published and val == 'DRAFT': continue
            _, btn_icon = status_colors.get(val, ('#64748b', str(val[0])))
            update_url = reverse('admin:project_set_status', args=[obj.pk])
            label_display = label
            if val == 'LIVE':
                label_display = 'Live / Official' if obj.is_published else 'Live (Playground)'
                
            buttons_html += f'''
                <button type="button" 
                        onclick="quickUpdateStatus(this, '{update_url}', '{val}', '{label}')"
                        title="Change to {label}"
                        class="status-panel-custom-btn">
                    <span>{btn_icon}</span> <span class="truncate">{label_display}</span>
                </button>
            '''
        actions_panel = ""
        if not obj.is_published:
            nuke_url = reverse('admin:project_nuke_data', args=[obj.pk])
            launch_url = reverse('admin:project_launch_data', args=[obj.pk])
            clone_url = reverse('admin:project_quick_clone', args=[obj.pk])
            actions_panel = f'''
                <div class="mt-4">
                    <button type="button" onclick="quickLaunchProject(this, '{launch_url}')" title="Lock project and Launch it to Production" class="launch-official-btn">🚀 LAUNCH OFFICIAL</button>
                    <button type="button" onclick="quickNukeProject(this, '{nuke_url}')" title="Delete all practice annotations" class="nuke-test-data-btn">🗑️ Nuke Test Data</button>
                    <button type="button" onclick="quickCloneProject(this, \'{clone_url}\', \'{obj.name}\', false)" title="Clone this project" class="clone-project-btn">📋 Clone Project</button>
                    <button type="button" onclick="quickRunMace(this, '{reverse('admin:project_run_mace', args=[obj.pk])}')" title="Calculate Annotator Reliability (MACE)" class="run-mace-btn">🤖 Run MACE Analysis</button>
                </div>
            '''
        else:
            clone_url = reverse('admin:project_quick_clone', args=[obj.pk])
            mace_url = reverse('admin:project_run_mace', args=[obj.pk])
            actions_panel = f'''
                <div class="mt-4 flex flex-col items-center gap-2">
                    <span class="officially-published-badge">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                        OFFICIALLY PUBLISHED
                    </span>
                    <button type="button" onclick="quickCloneProject(this, \'{clone_url}\', \'{obj.name}\', true)" title="Clone this project" class="clone-project-btn">📋 Edit/Clone Project</button>
                    <button type="button" onclick="quickRunMace(this, '{mace_url}')" title="Calculate Annotator Reliability (MACE)" class="run-mace-btn">🤖 Run MACE Analysis</button>
                </div>
            '''
        return mark_safe(
            f'<div class="status-badge-container flex flex-col w-[200px] max-w-[250px]">'
            f'  <div class="flex items-center justify-between mb-3">'
            f'      <span class="text-[11px] font-semibold opacity-60 uppercase">Current State</span>'
            f'      <span class="status-indicator" style="background: {bg_color}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; display: flex; align-items: center; gap: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">'
            f'          {icon} {obj.status}'
            f'      </span>'
            f'  </div>'
            f'  <div class="text-[10px] opacity-50 mb-1.5 font-semibold">TRANSITION TO:</div>'
            f'  <div class="flex gap-1.5 w-full">'
            f'      {buttons_html}'
            f'  </div>'
            f'  {actions_panel}'
            f'</div>'
        )

    @admin.display(description="Documents")
    def documents_link(self, obj):
        count = obj.documents.filter(is_gold_unit=False).count()
        url = reverse("admin:annotation_documentproxy_changelist") + "?" + urlencode({"project__id": f"{obj.id}", "o": "1"})
        return format_html('<a href="{}" class="admin-doc-link" style="background:#4f46e5; color:white; padding:7px 14px; border-radius:10px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:6px; min-width:140px;" onmouseover="this.style.background=\'#4338ca\'" onmouseout="this.style.background=\'#4f46e5\'"><span style="font-size:14px;">📄</span> <span>({}) Documents</span></a>', url, count)

    @admin.display(description="Gold Units")
    def gold_units_link(self, obj):
        count = obj.documents.filter(is_gold_unit=True).count()
        url = reverse("admin:annotation_goldunitproxy_changelist") + "?" + urlencode({"project__id": f"{obj.id}", "o": "1"})
        return format_html('<a href="{}" class="admin-gold-link" style="background:#eab308; color:white; padding:7px 14px; border-radius:10px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:6px; min-width:140px;" onmouseover="this.style.background=\'#ca8a04\'" onmouseout="this.style.background=\'#eab308\'"><span style="font-size:14px;">🛡️</span> <span>({}) Gold Units</span></a>', url, count)

    @admin.display(description="Annotations", ordering='-created_at')
    def annotations_link(self, obj):
        count = Annotation.objects.filter(document__project=obj, is_test=False).count()
        url = reverse("admin:annotation_annotation_changelist") + "?" + urlencode({"document__project__id": f"{obj.id}", "o": "1", "category": "regular"})
        bg = "#10b981" if count > 0 else "#64748b"
        return format_html('<a href="{}" style="background:{}; color:white; padding:7px 14px; border-radius:10px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:6px; min-width:140px;" title="Manage Annotations"><span style="font-size:14px;">📊</span> <span>({}) Annotations</span></a>', url, bg, count)

    @admin.display(description="Workers")
    def enrollments_link(self, obj):
        count = obj.enrollments.filter(annotator__is_test=False).count()
        url = reverse("admin:annotation_projectenrollment_changelist") + "?" + urlencode({"project__id": f"{obj.id}"})
        return format_html('<a href="{}" style="background:#8b5cf6; color:white; padding:6px 14px; border-radius:10px; font-size:11px; font-weight:700; text-decoration:none; display:inline-flex; align-items:center; gap:6px; min-width:140px;" title="Manage Workers"><span style="font-size:14px;">👥</span> <span>({}) Workers</span></a>', url, count)

    @admin.display(description="Participant Link & Preview")
    def link_prolific(self, obj):
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
        full_url = f"{base_url}/{obj.slug}?PROLIFIC_PID="
        input_id = f"preview_pid_{obj.pk}"
        is_pub_js = str(obj.is_published).lower()
        return format_html(
            '''
            <div style="display: flex; flex-direction: column; gap: 8px; min-width: 210px; padding: 4px;">
                <div style="display: flex; align-items: center; gap: 6px;">
                    <code style="background: rgba(0,0,0,0.3); padding: 5px 8px; border-radius: 6px; font-size: 10px; flex: 1; border: 1px solid rgba(255,255,255,0.1); color: #f8fafc; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{}</code>
                    <button type="button" onclick="navigator.clipboard.writeText(\'{}\'); if(window.adminNotify) window.adminNotify(\'info\', \'Link\', \'Copied!\')" 
                            style="background: #334155; border: 1px solid #475569; padding: 4px 6px; border-radius: 6px; cursor: pointer; color: white; font-size: 10px;">📋</button>
                </div>
                <div style="display: flex; flex-direction: column; gap: 4px; background: rgba(255,255,255,0.03); padding: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                    <label style="font-size: 10px; font-weight: 700; color: #cbd5e1; text-transform: uppercase;">Simulation Prolific PID</label>
                    <div style="display: flex; gap: 4px;">
                        <input type="text" id="{}" value="ADMIN_TEST" style="flex: 1; padding: 6px 8px; border: 1px solid #475569; border-radius: 6px; font-size: 11px; background: #0f172a; color: white; outline: none;">
                        <button type="button" onclick="window.openProjectPreview(\'{}\', \'{}\', \'{}\', {})"
                                style="background: #3b82f6; color: white; border: none; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-weight: 700; font-size: 11px;">👁️ Test as Participant</button>
                    </div>
                </div>
            </div>
            ''',
            full_url, full_url, input_id, base_url, obj.slug, input_id, is_pub_js
        )

    def save_model(self, request, obj, form, change):
        is_new = not obj.pk
        old_status = None
        if not is_new:
            old_status = Project.objects.get(pk=obj.pk).status
            
        # 1. Save base form data
        super(ProjectAdmin, self).save_model(request, obj, form, change)
        
        # 2. Create logs
        if is_new:
            ProjectLogEntry.objects.create(project=obj, action="Project Created", details=f"Project '{obj.name}' initialized.")
        elif old_status != obj.status:
            ProjectLogEntry.objects.create(project=obj, action="Status Changed", details=f"Status changed from {old_status} to {obj.status}.")

        # 3. File uploads (YAML) — Explicit mapping Form -> Database
        #
        # Deliberate order: annotation_schema first, practice_task after.
        # This ensures that when practice vs schema is validated,
        # obj.annotation_schema is already updated if both are uploaded together.
        #
        # upload_task_config   → validate structure as annotation_schema (hard error)
        # practice_task_config → validate gold_solution against schema (hard error → NOT saved)
        # upload_screening_config → no validation
        yaml_fields_mapping = {
            'upload_task_config':          'annotation_schema',
            'upload_screening_config':     'screening_config',
            'upload_practice_task_config': 'practice_task_config',
        }

        for form_field, db_field in yaml_fields_mapping.items():
            f = form.cleaned_data.get(form_field)
            if not f:
                continue

            # ── Parse YAML ────────────────────────────────────────────────
            validate_as_schema = (db_field == 'annotation_schema')
            try:
                parsed = parse_yaml_upload(f, validate_as_schema=validate_as_schema)
            except ValueError as e:
                self.message_user(request, f"❌ Upload error for '{form_field}': {e}", level='error')
                continue

            # ── Practice task: warn-only if no gold_solution ──────────────
            if db_field == 'practice_task_config':
                gold_sol = parsed.get('gold_solution')
                if not gold_sol:
                    self.message_user(
                        request,
                        "⚠️ Practice task saved, but has no 'gold_solution' key — annotators will not receive feedback.",
                        level='warning',
                    )

            # ── annotation_schema: warn if existing practice task is now stale ──
            # (blocking already happened in form.clean(), this is just an info reminder)
            elif db_field == 'annotation_schema' and 'upload_practice_task_config' not in form.changed_data:
                existing_practice = obj.practice_task_config or {}
                gold_sol = existing_practice.get('gold_solution')
                if existing_practice and gold_sol:
                    errs, _ = validate_gold_solution(gold_sol, parsed)
                    if errs:
                        self.message_user(
                            request,
                            "⚠️ The new annotation schema may be incompatible with the existing practice task. "
                            "Please re-upload the practice task to fix: "
                            + "; ".join(errs),
                            level='warning',
                        )

            # ── Persist ───────────────────────────────────────────────────
            setattr(obj, db_field, parsed)
            obj.save()

        # 4. File uploads (Markdown) - Explicit mapping Form -> Database
        markdown_fields_mapping = {
            'upload_codebook_content': 'codebook_content',
            'upload_instructions_content': 'instructions_content',
            'upload_informed_consent_content': 'informed_consent_config',
        }

        for form_field, db_field in markdown_fields_mapping.items():
            f = form.cleaned_data.get(form_field)
            if f:
                setattr(obj, db_field, f.read().decode('utf-8'))
                obj.save()

        # 5. Dataset processing
        if 'documents_file' in form.changed_data and obj.documents_file:
            process_uploaded_dataset(obj, obj.documents_file)
        if 'gold_units_file' in form.changed_data and obj.gold_units_file:
            process_uploaded_dataset(obj, obj.gold_units_file)

