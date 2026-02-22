from .project import ProjectAdmin
from .document import DocumentAdmin
from .annotator import AnnotatorAdmin
from .annotation import AnnotationAdmin
from .enrollment import ProjectEnrollmentAdmin
from django.contrib.auth.models import Group
from django.contrib import admin


admin.site.unregister(Group)