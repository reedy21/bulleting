"""WebSocket для аукционов: обновление текущей цены и истории ставок в реальном времени."""

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from .auction_services import get_auction_base, get_auction_step, get_min_bid, is_auction_active, place_bid
from .models import Advertisement

User = get_user_model()


class AuctionConsumer(AsyncWebsocketConsumer):
    """
    Канал аукциона: ws/auction/<ad_id>/

    Действия: place_bid (amount), refresh.
    История ставок передаётся только автору объявления.
    """

    async def connect(self):
        self.user = self.scope['user']
        self.ad_id = self.scope['url_route']['kwargs']['ad_id']
        self.room_group_name = f'auction_{self.ad_id}'

        ad = await self._get_ad()
        if ad is None or ad.ad_type != Advertisement.AdType.AUCTION:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        state = await self._auction_state()
        await self.send(text_data=json.dumps({'type': 'state', **state}))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            payload = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            await self._send_error('Некорректный JSON.')
            return

        action = payload.get('action')
        if action == 'place_bid':
            await self._handle_bid(payload)
        elif action == 'refresh':
            state = await self._auction_state()
            await self.send(text_data=json.dumps({'type': 'state', **state}))

    async def _handle_bid(self, payload):
        if not self.user.is_authenticated:
            await self._send_error('Войдите, чтобы сделать ставку.')
            return

        amount = payload.get('amount')
        result = await self._place_bid_sync(amount)
        if result.get('error'):
            await self._send_error(result['error'])
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'bid_update', 'payload': result},
        )

    async def bid_update(self, event):
        payload = dict(event['payload'])
        bid = payload.pop('bid', None)
        if bid and await self._is_author():
            payload['bid'] = bid
        await self.send(text_data=json.dumps({'type': 'bid', **payload}))

    async def auction_finished(self, event):
        await self.send(text_data=json.dumps({'type': 'finished', **event['payload']}))

    async def _send_error(self, detail: str):
        await self.send(text_data=json.dumps({'type': 'error', 'detail': detail}))

    @database_sync_to_async
    def _get_ad(self):
        try:
            return Advertisement.objects.get(pk=self.ad_id, is_active=True)
        except Advertisement.DoesNotExist:
            return None

    @database_sync_to_async
    def _is_author(self) -> bool:
        if not self.user.is_authenticated:
            return False
        return Advertisement.objects.filter(pk=self.ad_id, author_id=self.user.pk).exists()

    @database_sync_to_async
    def _place_bid_sync(self, amount) -> dict:
        try:
            ad = Advertisement.objects.get(pk=self.ad_id)
            bid = place_bid(ad, self.user, amount)
            ad.refresh_from_db()
            payload = {
                'current_price': str(int(ad.current_price)),
                'min_bid': str(int(get_min_bid(ad))),
                'bid': {
                    'id': bid.pk,
                    'amount': str(int(bid.amount)),
                    'bidder': bid.bidder.username,
                    'created_at': bid.created_at.isoformat(),
                },
                'active': is_auction_active(ad),
                'finished': ad.auction_finished,
            }
            return payload
        except ValueError as exc:
            return {'error': str(exc)}

    @database_sync_to_async
    def _auction_state(self) -> dict:
        ad = Advertisement.objects.select_related('auction_winner', 'author').get(pk=self.ad_id)
        last_bid = ad.bids.select_related('bidder').order_by('-created_at').first()
        state = {
            'active': is_auction_active(ad),
            'finished': ad.auction_finished,
            'current_price': str(int(ad.current_price or get_auction_base(ad))),
            'min_bid': str(int(get_min_bid(ad))),
            'auction_base': get_auction_base(ad),
            'auction_step': get_auction_step(ad),
            'auction_end': ad.auction_end.isoformat() if ad.auction_end else None,
            'winner': ad.auction_winner.username if ad.auction_winner_id else None,
            'last_bidder': last_bid.bidder.username if last_bid else None,
        }
        user = self.user
        if user.is_authenticated and ad.author_id == user.id:
            state['bids'] = [
                {
                    'id': b.pk,
                    'amount': str(int(b.amount)),
                    'bidder': b.bidder.username,
                    'created_at': b.created_at.isoformat(),
                }
                for b in ad.bids.select_related('bidder').order_by('-created_at')[:15]
            ]
        return state
