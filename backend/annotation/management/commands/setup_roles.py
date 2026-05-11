from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from annotation.models import Project, Annotator, Document, Annotation, ProjectEnrollment

class Command(BaseCommand):
    help = 'Setup default roles (Collaborator and Owner) with appropriate permissions'

    def handle(self, *args, **options):
        # 1. Define groups
        groups_config = {
            'Collaborator': [
                ('view', Project),
                ('change', Project),
                ('view', Annotator),
                ('view', Document),
                ('view', Annotation),
                ('view', ProjectEnrollment),
            ],
            'Owner': [
                ('add', Project),
                ('view', Project),
                ('change', Project),
                ('delete', Project),
                ('view', Annotator),
                ('add', Document),
                ('view', Document),
                ('change', Document),
                ('delete', Document),
                ('view', Annotation),
                ('view', ProjectEnrollment),
                ('add', ProjectEnrollment),
                ('change', ProjectEnrollment),
                ('delete', ProjectEnrollment),
            ]
        }

        for group_name, perms_list in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created group: {group_name}'))
            else:
                self.stdout.write(f'Group {group_name} already exists, updating permissions...')

            # Clear existing permissions to ensure a clean state (optional, but safer for "setup")
            group.permissions.clear()

            for action, model in perms_list:
                content_type = ContentType.objects.get_for_model(model)
                codename = f'{action}_{model._meta.model_name}'
                try:
                    permission = Permission.objects.get(content_type=content_type, codename=codename)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Permission {codename} not found for {model._meta.model_name}'))

        self.stdout.write(self.style.SUCCESS('Role setup completed successfully.'))
