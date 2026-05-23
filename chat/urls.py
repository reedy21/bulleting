from django.urls import path

from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('<int:pk>/', views.chat_room, name='chat_room'),
    path('start/<int:ad_pk>/', views.start_chat, name='start_chat'),
    path('api/unread/', views.unread_count_api, name='unread_count_api'),
]
