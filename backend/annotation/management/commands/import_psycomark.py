import json
import os
from django.core.management.base import BaseCommand
from annotation.models import Project, Document

class Command(BaseCommand):
    help = 'Imports the PsyCoMark redacted dataset (JSONL) with placeholder text.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the .jsonl file')
        parser.add_argument('--project_id', type=int, required=True, help='ID of the Project to assign documents to')

    def handle(self, *args, **options):
        file_path = options['file_path']
        project_id = options['project_id']

        # 1. Validation: Check if Project exists
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:  # ty:ignore[unresolved-attribute]
            self.stdout.write(self.style.ERROR(f"Project with ID {project_id} not found."))
            return

        # 2. Validation: Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Starting import for Project: {project.name}...")
        
        count_created = 0
        count_skipped = 0

        # 3. Reading the JSONL file line by line
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                try:
                    data = json.loads(line)
                    
                    external_id = data.get('_id')
                    subreddit = data.get('subreddit')
                    
                    text_content = data.get('text') 
                    
                    if not text_content:
                        text_content = "[ERROR] Missing text in JSON"
                    
                    Document.objects.get_or_create(
                        external_id=external_id,
                        project=project,
                        defaults={
                            'text': text_content,
                            'metadata': {'subreddit': subreddit},
                            'is_gold_unit': False,
                            'gold_solution': None,
                            'min_annotations_required': 3
                        }
                    )
                    
                    count_created += 1

                except json.JSONDecodeError:
                    self.stdout.write(self.style.WARNING(f"Skipping line {line_num}: Invalid JSON"))
                    continue

        # 4. Final Report
        self.stdout.write(self.style.SUCCESS(
            f"IMPORT COMPLETE!\n"
            f"- Created: {count_created}\n"
            f"- Skipped (Already existed): {count_skipped}\n"
            f"- Total scanned: {line_num + 1}"
        ))