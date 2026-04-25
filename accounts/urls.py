"""Маршруты приложения accounts: регистрация, вход, выход, кабинет."""
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('cabinet/', views.cabinet, name='cabinet'),
    path('profile/', views.profile, name='profile'),
    path('favorites/', views.favorites, name='favorites'),
]
