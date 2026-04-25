"""Маршруты общих страниц (главная и т.д.)."""
from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
]
