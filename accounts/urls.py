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
    path('profile/auctions/', views.my_auctions, name='my_auctions'),
    path('profile/auctions/participating/', views.participating_auctions, name='participating_auctions'),
    path('favorites/', views.favorites, name='favorites'),
    path('history/', views.view_history, name='view_history'),
    path('notifications/', views.notifications, name='notifications'),
]
