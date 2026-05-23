from ads.models import UserNotification


def get_user_display_name(user) -> str:
    """Имя для шапки и заголовка профиля: ФИО или логин."""
    if not user.is_authenticated:
        return ''
    full = user.get_full_name().strip()
    return full or user.username


def user_profile_context(request):
    """Имя пользователя и счётчик непрочитанных уведомлений."""
    name = get_user_display_name(request.user)
    unread_notifications = 0
    if request.user.is_authenticated:
        unread_notifications = UserNotification.objects.filter(
            user=request.user, is_read=False
        ).count()
    return {
        'user_display_name': name,
        'unread_notifications_count': unread_notifications,
    }
