"""Вспомогательная логика чатов: создание диалога и подсчёт непрочитанных."""

from django.db.models import Q

from ads.models import Advertisement

from .models import Chat, Message


def get_or_create_chat(advertisement: Advertisement, buyer) -> Chat:
    """
    Получить или создать чат между покупателем и автором объявления.

    Продавец всегда author объявления.
    """
    chat, _ = Chat.objects.get_or_create(
        advertisement=advertisement,
        buyer=buyer,
        defaults={'seller': advertisement.author},
    )
    return chat


def user_chats_queryset(user):
    """Все чаты, в которых участвует пользователь."""
    return (
        Chat.objects.filter(Q(buyer=user) | Q(seller=user))
        .select_related('advertisement', 'buyer', 'seller', 'advertisement__author')
        .prefetch_related('advertisement__photos')
    )


def unread_messages_count(user) -> int:
    """Количество непрочитанных входящих сообщений для badge в шапке."""
    if not user.is_authenticated:
        return 0
    chat_ids = user_chats_queryset(user).values_list('pk', flat=True)
    return Message.objects.filter(
        chat_id__in=chat_ids,
        is_read=False,
        is_deleted=False,
    ).exclude(sender=user).count()
