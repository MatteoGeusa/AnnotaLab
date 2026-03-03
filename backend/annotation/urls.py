# backend/core/urls.py

from django.urls import path
from .views import (
    InitializeSession, GetNextTask, SubmitAnnotation, 
    AcceptConsent, CompleteOnboarding, GetConsent,
    GetScreening, SubmitScreening
)

urlpatterns = [
    path('session/', InitializeSession.as_view(), name='session'),
    path('consent/', AcceptConsent.as_view(), name='consent'),
    path('get-consent/', GetConsent.as_view(), name='get_consent'),
    path('screening/', SubmitScreening.as_view(), name='screening'),
    path('get-screening/', GetScreening.as_view(), name='get_screening'),
    path('onboarding/', CompleteOnboarding.as_view(), name='onboarding'),
    path('next-task/', GetNextTask.as_view(), name='next_task'),
    path('submit/', SubmitAnnotation.as_view(), name='submit'),
]