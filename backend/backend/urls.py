"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def healthcheck(request):
    return JsonResponse({"message": "OK"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/healthcheck', healthcheck),
    path('api/v1/', include('annotation.urls')),
]
