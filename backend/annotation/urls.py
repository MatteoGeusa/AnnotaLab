# backend/core/urls.py

from django.urls import path
from .views import InitializeSession, GetNextTask, SubmitAnnotation, AcceptConsent, CompleteOnboarding, SubmitSurvey

urlpatterns = [
    path('session/', InitializeSession.as_view(), name='session'),
    path('consent/', AcceptConsent.as_view(), name='consent'),
    path('onboarding/', CompleteOnboarding.as_view(), name='onboarding'),
    path('next-task/', GetNextTask.as_view(), name='next_task'),
    path('submit/', SubmitAnnotation.as_view(), name='submit'),
    path('submit-survey/', SubmitSurvey.as_view(), name='submit_survey'),
]