"""Уведомления о непрочитанных сообщениях через channel layer."""

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .services import unread_messages_count


def notify_user(user_id: int, extra: dict | None = None) -> None:
    """Отправить пользователю обновление счётчика непрочитанных."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    payload = {
        'type': 'notify',
        'count': unread_messages_count_by_id(user_id),
    }
    if extra:
        payload.update(extra)
    async_to_sync(channel_layer.group_send)(f'user_{user_id}', payload)


def unread_messages_count_by_id(user_id: int) -> int:
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return 0
    return unread_messages_count(user)
