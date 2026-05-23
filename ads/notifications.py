"""Создание и доставка in-app уведомлений (WebSocket + БД)."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.urls import reverse

from .models import Advertisement, UserNotification


def _broadcast(user_id: int, payload: dict) -> None:
    layer = get_channel_layer()
    if not layer:
        return
    async_to_sync(layer.group_send)(
        f'user_{user_id}',
        {'type': 'user_notification', 'payload': payload},
    )


def create_notification(
    user,
    notification_type: str,
    title: str,
    message: str,
    advertisement=None,
) -> UserNotification:
    """Сохранить уведомление и отправить по WebSocket."""
    url = ''
    if advertisement:
        url = reverse('ads:ad_detail', kwargs={'pk': advertisement.pk})

    notification = UserNotification.objects.create(
        user=user,
        advertisement=advertisement,
        notification_type=notification_type,
        title=title,
        message=message,
    )

    unread = UserNotification.objects.filter(user=user, is_read=False).count()
    _broadcast(
        user.pk,
        {
            'notification_type': notification_type,
            'title': title,
            'message': message,
            'url': url,
            'unread_notifications': unread,
            'id': notification.pk,
        },
    )
    return notification


def notify_auction_winner(advertisement: Advertisement) -> None:
    """Победителю — выигрыш аукциона."""
    if not advertisement.auction_winner_id:
        return
    winner = advertisement.auction_winner
    price = int(advertisement.current_price or 0)
    create_notification(
        winner,
        UserNotification.NotificationType.AUCTION_WON,
        'Вы выиграли аукцион',
        f'«{advertisement.title}» — ваша ставка {price} ₽. Свяжитесь с продавцом.',
        advertisement,
    )


def notify_auction_author(advertisement: Advertisement) -> None:
    """Автору — итоги завершённого аукциона."""
    if advertisement.auction_winner_id:
        message = (
            f'«{advertisement.title}» завершён. '
            f'Победитель: {advertisement.auction_winner.username}, '
            f'ставка {int(advertisement.current_price or 0)} ₽.'
        )
    else:
        message = f'«{advertisement.title}» завершён. Ставок не было.'
    create_notification(
        advertisement.author,
        UserNotification.NotificationType.AUCTION_ENDED,
        'Аукцион завершён',
        message,
        advertisement,
    )
