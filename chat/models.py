from django.conf import settings
from django.db import models


class Chat(models.Model):
    """
    Диалог между покупателем и автором объявления.

    Один чат на пару (объявление + покупатель): продавец всегда author объявления.
    """

    advertisement = models.ForeignKey(
        'ads.Advertisement',
        verbose_name='объявление',
        on_delete=models.CASCADE,
        related_name='chats',
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='покупатель',
        on_delete=models.CASCADE,
        related_name='chats_as_buyer',
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='продавец',
        on_delete=models.CASCADE,
        related_name='chats_as_seller',
    )
    created_at = models.DateTimeField('создан', auto_now_add=True)
    updated_at = models.DateTimeField('обновлён', auto_now=True)

    class Meta:
        verbose_name = 'чат'
        verbose_name_plural = 'чаты'
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['advertisement', 'buyer'],
                name='unique_chat_per_ad_buyer',
            )
        ]

    def __str__(self) -> str:
        return f'Чат #{self.pk} — {self.advertisement.title}'

    def involves_user(self, user) -> bool:
        """Проверка, что пользователь — участник чата."""
        return user.pk in (self.buyer_id, self.seller_id)

    def other_participant(self, user):
        """Второй участник диалога относительно текущего пользователя."""
        return self.seller if user.pk == self.buyer_id else self.buyer


class Message(models.Model):
    """Сообщение в чате с поддержкой прочтения, редактирования и мягкого удаления."""

    chat = models.ForeignKey(
        Chat,
        verbose_name='чат',
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='отправитель',
        on_delete=models.CASCADE,
        related_name='chat_messages',
    )
    text = models.TextField('текст')
    created_at = models.DateTimeField('отправлено', auto_now_add=True)
    updated_at = models.DateTimeField('изменено', auto_now=True)
    is_read = models.BooleanField('прочитано', default=False)
    is_edited = models.BooleanField('отредактировано', default=False)
    is_deleted = models.BooleanField('удалено', default=False)

    class Meta:
        verbose_name = 'сообщение'
        verbose_name_plural = 'сообщения'
        ordering = ['created_at']

    def __str__(self) -> str:
        preview = self.text[:40] + '…' if len(self.text) > 40 else self.text
        return f'{self.sender}: {preview}'
