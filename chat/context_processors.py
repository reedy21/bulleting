from .services import unread_messages_count


def chat_notifications(request):
    """Непрочитанные сообщения для отображения в навигации."""
    return {'unread_messages_count': unread_messages_count(request.user)}
