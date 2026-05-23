import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import Chat, Message


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket-обработчик чата: отправка, редактирование, удаление, отметка прочитанным.

    URL: ws/chat/<chat_id>/
    """

    async def connect(self):
        self.user = self.scope['user']
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        if not self.user.is_authenticated:
            await self.close()
            return

        chat = await self._get_chat()
        if chat is None or not chat.involves_user(self.user):
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # При входе в чат помечаем входящие сообщения прочитанными
        read_ids = await self._mark_incoming_as_read()
        if read_ids:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'messages_read',
                    'message_ids': read_ids,
                    'reader_id': self.user.pk,
                },
            )

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            payload = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            await self._send_error('Некорректный формат данных.')
            return

        action = payload.get('action')
        if action == 'send':
            await self._handle_send(payload)
        elif action == 'edit':
            await self._handle_edit(payload)
        elif action == 'delete':
            await self._handle_delete(payload)
        elif action == 'mark_read':
            read_ids = await self._mark_incoming_as_read()
            if read_ids:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'messages_read',
                        'message_ids': read_ids,
                        'reader_id': self.user.pk,
                    },
                )
        else:
            await self._send_error('Неизвестное действие.')

    async def _handle_send(self, payload):
        text = (payload.get('text') or '').strip()
        if not text:
            await self._send_error('Сообщение не может быть пустым.')
            return
        if len(text) > 4000:
            await self._send_error('Сообщение слишком длинное (макс. 4000 символов).')
            return

        message = await self._create_message(text)
        if message is None:
            await self._send_error('Не удалось отправить сообщение.')
            return

        serialized = self._serialize_message(message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'chat_message', 'message': serialized},
        )
        await self._notify_recipient(serialized)

    async def _handle_edit(self, payload):
        message_id = payload.get('message_id')
        text = (payload.get('text') or '').strip()
        if not message_id or not text:
            await self._send_error('Укажите сообщение и новый текст.')
            return

        message = await self._edit_message(message_id, text)
        if message is None:
            await self._send_error('Редактирование недоступно.')
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'message_edited', 'message': self._serialize_message(message)},
        )

    async def _handle_delete(self, payload):
        message_id = payload.get('message_id')
        if not message_id:
            await self._send_error('Укажите сообщение для удаления.')
            return

        message = await self._delete_message(message_id)
        if message is None:
            await self._send_error('Удаление недоступно.')
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'message_deleted', 'message': self._serialize_message(message)},
        )

    # --- Обработчики событий группы ---

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'type': 'message', 'message': event['message']}))

    async def message_edited(self, event):
        await self.send(text_data=json.dumps({'type': 'edited', 'message': event['message']}))

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({'type': 'deleted', 'message': event['message']}))

    async def messages_read(self, event):
        if event.get('reader_id') == self.user.pk:
            return
        await self.send(
            text_data=json.dumps(
                {'type': 'read', 'message_ids': event['message_ids'], 'reader_id': event['reader_id']}
            )
        )

    async def _send_error(self, detail: str):
        await self.send(text_data=json.dumps({'type': 'error', 'detail': detail}))

    def _serialize_message(self, message: Message) -> dict:
        return {
            'id': message.pk,
            'text': message.text if not message.is_deleted else '',
            'sender_id': message.sender_id,
            'sender_username': message.sender.username,
            'created_at': message.created_at.isoformat(),
            'updated_at': message.updated_at.isoformat(),
            'is_read': message.is_read,
            'is_edited': message.is_edited,
            'is_deleted': message.is_deleted,
        }

    @database_sync_to_async
    def _get_chat(self):
        try:
            return Chat.objects.get(pk=self.chat_id)
        except Chat.DoesNotExist:
            return None

    @database_sync_to_async
    def _create_message(self, text: str):
        try:
            chat = Chat.objects.get(pk=self.chat_id)
        except Chat.DoesNotExist:
            return None
        if not chat.involves_user(self.user):
            return None
        message = Message.objects.create(chat=chat, sender=self.user, text=text)
        Chat.objects.filter(pk=chat.pk).update(updated_at=timezone.now())
        message = Message.objects.select_related('sender').get(pk=message.pk)
        return message

    @database_sync_to_async
    def _edit_message(self, message_id, text: str):
        try:
            message = Message.objects.select_related('sender', 'chat').get(
                pk=message_id, chat_id=self.chat_id, sender=self.user, is_deleted=False
            )
        except Message.DoesNotExist:
            return None
        message.text = text
        message.is_edited = True
        message.save(update_fields=['text', 'is_edited', 'updated_at'])
        return message

    @database_sync_to_async
    def _delete_message(self, message_id):
        try:
            message = Message.objects.select_related('sender').get(
                pk=message_id, chat_id=self.chat_id, sender=self.user, is_deleted=False
            )
        except Message.DoesNotExist:
            return None
        message.is_deleted = True
        message.text = ''
        message.save(update_fields=['is_deleted', 'text', 'updated_at'])
        return message

    async def _notify_recipient(self, serialized: dict):
        """Обновить badge и список чатов у собеседника."""
        chat = await self._get_chat()
        if chat is None:
            return
        other = chat.other_participant(self.user)
        preview = serialized.get('text', '')[:80]
        await self.channel_layer.group_send(
            f'user_{other.pk}',
            {
                'type': 'notify',
                'count': await self._unread_for_user(other.pk),
                'chat_id': self.chat_id,
                'preview': preview,
            },
        )

    @database_sync_to_async
    def _unread_for_user(self, user_id: int) -> int:
        from .notifications import unread_messages_count_by_id

        return unread_messages_count_by_id(user_id)

    @database_sync_to_async
    def _mark_incoming_as_read(self):
        qs = Message.objects.filter(
            chat_id=self.chat_id,
            is_read=False,
            is_deleted=False,
        ).exclude(sender=self.user)
        ids = list(qs.values_list('pk', flat=True))
        if ids:
            qs.update(is_read=True)
        return ids
