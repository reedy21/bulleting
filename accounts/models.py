from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Пользователь доски объявлений.

    Наследуемся от AbstractUser, чтобы в будущем добавлять свои поля
    (телефон, город, аватар и т.д.) без ломки стандартной авторизации Django.
    """

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
