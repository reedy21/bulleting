"""Маршруты объявлений (список и детали — доработка в следующих спринтах)."""
from django.urls import path

from . import views

app_name = 'ads'

urlpatterns = [
    path('', views.ad_list, name='ad_list'),
    path('create/', views.create_ad, name='create_ad'),
    path('<int:pk>/', views.ad_detail, name='ad_detail'),
    path('<int:pk>/edit/', views.edit_ad, name='edit_ad'),
    path('<int:pk>/delete/', views.delete_ad, name='delete_ad'),
    path('<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
]
