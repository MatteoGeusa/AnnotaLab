"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path
from django.http import JsonResponse

def api_test(request):
    return JsonResponse({"messaggio": "Ciao! Sono Django e sto parlando con Vue!"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/test', api_test), # api di testing non esiste una view per questo endpoint
]
