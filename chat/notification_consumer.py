"""WebSocket уведомлений: badge непрочитанных без перезагрузки страницы."""

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .services import unread_messages_count


class NotificationConsumer(AsyncWebsocketConsumer):
    """Персональный канал: ws/notifications/"""

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return
        self.group_name = f'user_{self.user.pk}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        count = await self._unread_count()
        await self.send(text_data=json.dumps({'type': 'unread', 'count': count}))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notify(self, event):
        """Событие от channel layer при новом сообщении."""
        await self.send(
            text_data=json.dumps(
                {
                    'type': 'unread',
                    'count': event.get('count', 0),
                    'chat_id': event.get('chat_id'),
                    'preview': event.get('preview'),
                }
            )
        )

    async def user_notification(self, event):
        """In-app уведомление (аукцион и др.)."""
        payload = event.get('payload', {})
        await self.send(
            text_data=json.dumps(
                {
                    'type': 'notification',
                    **payload,
                }
            )
        )

    @database_sync_to_async
    def _unread_count(self):
        return unread_messages_count(self.user)
