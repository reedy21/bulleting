from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/auction/<int:ad_id>/', consumers.AuctionConsumer.as_asgi()),
]
