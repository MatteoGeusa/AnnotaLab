from django.contrib import admin
from django.db.models import Count
from .models import Project, Document, Annotator, Annotation
from import_export import resources
from import_export.admin import ImportExportModelAdmin

# 1. PROJECT Configuration (Batch)
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'doc_count')  # Visible columns
    search_fields = ('name',)                           # Search bar

    # Function to count how many documents are in the batch
    @admin.display(description="No. Documents")
    def doc_count(self, obj):
        return obj.documents.count()
    


class DocumentResource(resources.ModelResource):
    class Meta:
        model = Document
        # Here we specify which CSV columns to read
        fields = ('id', 'text', 'external_id', 'project')

# 2. DOCUMENT Configuration
@admin.register(Document)
class DocumentAdmin(ImportExportModelAdmin):
    resource_class = DocumentResource
    list_display = ('id', 'short_text', 'project', 'current_annotations_count', 'is_completed')
    list_filter = ('project', 'min_annotations_required') # Useful side filters!
    search_fields = ('text', 'external_id')               # Search in text or original ID
    
    # To avoid showing kilometer-long texts in the list, we truncate them
    @admin.display(description="Text Preview")
    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    # A visual column (True/False) to see if it's finished
    @admin.display(boolean=True, description="Completed?")
    def is_completed(self, obj):
        return obj.current_annotations_count >= obj.min_annotations_required



# 3. ANNOTATOR Configuration
@admin.register(Annotator)
class AnnotatorAdmin(admin.ModelAdmin):
    list_display = ('prolific_pid', 'created_at', 'annotations_made')
    search_fields = ('prolific_pid',)

    @admin.display(description="Tasks Performed")
    def annotations_made(self, obj):
        return obj.annotations.count()

# 4. ANNOTATION Configuration (Results)
@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'annotator', 'created_at')
    list_filter = ('document__project',) # Filter annotations by Batch
    readonly_fields = ('created_at',)    # Avoid accidental date edits