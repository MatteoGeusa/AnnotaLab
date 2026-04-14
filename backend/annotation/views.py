from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Document, Annotator, Annotation, Project, ProjectEnrollment
from .serializers import DocumentSerializer, AnnotationSerializer
from .gold_strategies import check_gold_correctness
from .services import DistributionService

PROLIFIC_COMPLETION_URL = "https://app.prolific.com/submissions/complete?cc=TUO_CODICE_PROLIFIC"

class ProjectContextMixin:
    """
    Mixin to provide common project and annotator context resolution.
    """
    def get_context(self, request, is_query=False):
        data = request.query_params if is_query else request.data
        pid = data.get('prolific_pid') or data.get('pid')
        project_id = data.get('project_id')
        project_slug = data.get('project_slug')

        if not pid:
            return None, None, None, Response({"error": "Missing PID"}, status=400)
        
        if not project_id and not project_slug:
            return None, None, None, Response({"error": "Missing Project identification"}, status=400)
            
        if project_slug:
            project = get_object_or_404(Project, slug=project_slug)
        else:
            project = get_object_or_404(Project, id=project_id)

        annotator, _ = Annotator.objects.get_or_create(prolific_pid=pid)
        enrollment, _ = ProjectEnrollment.objects.get_or_create(project=project, annotator=annotator)
        
        return project, annotator, enrollment, None

class InitializeSession(ProjectContextMixin, APIView):
    def post(self, request):
        project, annotator, enrollment, error_response = self.get_context(request)
        if error_response: return error_response

        if not project.can_accept_annotations:
            msg = "This project is still in DRAF phase and not yet open." if project.status == 'DRAFT' else f"Project is currently {project.status.lower()}"
            return Response({"error": msg}, status=404)

        # Metadata extraction
        metadata = request.data.get('metadata', {})
        for key in ['project_id', 'prolific_pid', 'PROLIFIC_PID']:
            metadata.pop(key, None)
        
        if metadata:
            annotator.metadata.update(metadata)
            annotator.save()

        # Determine current step
        current_step = 'CONSENT'
        if enrollment.consent_accepted:
            has_screening = project.enable_screening and project.screening_config and len(project.screening_config) > 0
            if has_screening and not enrollment.screening_completed:
                current_step = 'SCREENING'
            elif project.enable_codebook and not enrollment.codebook_completed:
                current_step = 'CODEBOOK'
            elif (project.enable_instructions or project.enable_practice_task) and not enrollment.onboarding_completed:
                current_step = 'INSTRUCTIONS'
            else:
                current_step = 'ONBOARDING'
        
        if enrollment.onboarding_completed:
            current_step = 'ANNOTATION'
            if enrollment.status == 'PENDING':
                enrollment.status = 'ACTIVE'
                enrollment.save(update_fields=['status'])
            
        if enrollment.status == 'COMPLETED':
            current_step = 'COMPLETED'

        completion_url = PROLIFIC_COMPLETION_URL
        if project.prolific_completion_code:
            completion_url = f"https://app.prolific.com/submissions/complete?cc={project.prolific_completion_code}"

        return Response({
            "status": "ok",
            "step": current_step,
            "completion_url": completion_url if current_step == 'COMPLETED' else None
        })

class AcceptConsent(ProjectContextMixin, APIView):
    def post(self, request):
        project, annotator, enrollment, error_response = self.get_context(request)
        if error_response: return error_response
        
        enrollment.consent_accepted = True
        enrollment.save()
        return Response({"status": "ok", "next_step": "SCREENING"})

class GetCodebook(ProjectContextMixin, APIView):
    def get(self, request):
        project, annotator, enrollment, error_response = self.get_context(request, is_query=True)
        if error_response: return error_response
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        if not project.enable_codebook:
            return Response({"content": "", "skip": True})

        return Response({
            "content": project.codebook_content or "",
            "skip": False
        })

class CompleteCodebook(ProjectContextMixin, APIView):
    def post(self, request):
        project, annotator, enrollment, error_response = self.get_context(request)
        if error_response: return error_response
        
        enrollment.codebook_completed = True
        enrollment.save()
        return Response({"status": "ok", "next_step": "INSTRUCTIONS"})

class GetInstructions(ProjectContextMixin, APIView):
    def get(self, request):
        project, annotator, enrollment, error_response = self.get_context(request, is_query=True)
        if error_response: return error_response
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        if not project.enable_instructions and not project.enable_practice_task:
            return Response({"content": "", "skip": True})

        practice = project.practice_task_config or {}
        has_practice = bool(project.enable_practice_task and practice and practice.get('text'))
        practice_required = project.practice_task_required if has_practice else False

        return Response({
            "has_instructions": project.enable_instructions,
            "content": project.instructions_content or "",
            "practice_task": practice if has_practice else None,
            "practice_task_required": practice_required,
            "annotation_schema": project.annotation_schema or {},
            "skip": False
        })

class GetScreening(ProjectContextMixin, APIView):
    def get(self, request):
        project, annotator, enrollment, error_response = self.get_context(request, is_query=True)
        if error_response: return error_response
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        if enrollment.screening_completed:
            return Response({"error": "Screening already completed"}, status=400)

        if not project.enable_screening or not project.screening_config:
            return Response({"questions": [], "skip": True})

        return Response({
            "questions": project.screening_config,
            "skip": False
        })

class SubmitScreening(ProjectContextMixin, APIView):
    def post(self, request):
        project, annotator, enrollment, error_response = self.get_context(request)
        if error_response: return error_response

        responses = request.data.get('responses', {})
        screening_config = project.screening_config or []
        for question in screening_config:
            if question.get('required', False):
                q_id = question.get('id')
                if q_id not in responses or responses[q_id] in [None, '']:
                    label = question.get('label', q_id)
                    return Response({"error": f"Required field '{label}' is missing."}, status=400)

        annotator.metadata['screening_responses'] = responses
        annotator.save()
        
        enrollment.screening_completed = True
        enrollment.save()
        return Response({"status": "ok", "next_step": "ONBOARDING"})

class CompleteOnboarding(ProjectContextMixin, APIView):
    def post(self, request):
        project, annotator, enrollment, error_response = self.get_context(request)
        if error_response: return error_response

        enrollment.onboarding_completed = True
        screening_ok = enrollment.screening_completed or not project.enable_screening or not project.screening_config
        
        if enrollment.consent_accepted and screening_ok and enrollment.onboarding_completed:
            if enrollment.status == 'PENDING':
                enrollment.status = 'ACTIVE'
        
        enrollment.save()
        return Response({"status": "ok", "next_step": "ANNOTATION"})

class SubmitAnnotation(ProjectContextMixin, APIView):
    def post(self, request):
        project, annotator, enrollment, error_response = self.get_context(request)
        if error_response: return error_response
        
        serializer = AnnotationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    annotation = serializer.save(annotator=annotator)
                    document = annotation.document
                    
                    if document.is_gold_unit:
                        enrollment.gold_tasks_completed += 1
                        is_correct = check_gold_correctness(request.data.get('result', {}), document.gold_solution)
                        
                        from .gold_strategies import get_strategy
                        strategy = get_strategy()
                        gold_cfg = {
                            'min_accuracy_required': project.min_accuracy_required,
                            'min_gold_before_eval': project.min_gold_before_eval,
                        }
                        
                        should_exclude, _ = strategy(enrollment, gold_cfg, is_correct)
                        if should_exclude:
                            enrollment.status = 'EXCLUDED'
                        enrollment.save()

                return Response({"status": "saved"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetNextTask(ProjectContextMixin, APIView):
    def get(self, request):
        project, annotator, enrollment, error_response = self.get_context(request, is_query=True)
        if error_response: return error_response

        if not project.can_accept_annotations:
            return Response({"status": "stopped", "message": f"This project is currently {project.status.lower()} and not accepting annotations."})

        result = DistributionService.get_next_task(project, annotator, enrollment)
        
        if result['status'] == 'stopped':
            return Response({"status": "stopped", "message": result.get('message')})
        
        if result['status'] == 'completed':
            code = project.prolific_completion_code
            url = f"https://app.prolific.com/submissions/complete?cc={code}" if code else PROLIFIC_COMPLETION_URL
            return Response({"status": "completed", "completion_url": url})

        if result['status'] == 'retry':
            return Response({"status": "retry"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        doc = result['document']
        serializer = DocumentSerializer(doc)
        data = serializer.data 
        data.update({'is_gold': doc.is_gold_unit, 'feedback_enabled': False})
        return Response(data)

class GetConsent(ProjectContextMixin, APIView):
    def get(self, request):
        project, annotator, enrollment, error_response = self.get_context(request, is_query=True)
        if error_response: return error_response
        
        if not project.can_accept_annotations:
            return Response({"error": "Project is not active"}, status=404)
        
        if enrollment.consent_accepted:
            return Response({"error": "Already consented"}, status=400)

        return Response({"consent_text": project.informed_consent_config})