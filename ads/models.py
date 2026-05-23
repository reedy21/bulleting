from django.conf import settings
from django.db import models


class Category(models.Model):
    """
    Категория объявлений (например «Электроника», «Недвижимость»).

    Иерархия через parent опциональна: подкатегории можно добавить позже.
    """

    # Человекочитаемое название, показывается в интерфейсе и в админке.
    name = models.CharField('название', max_length=120)

    # Уникальный фрагмент URL; удобен для ЧПУ и фильтров (см. следующие спринты).
    slug = models.SlugField('слаг', max_length=140, unique=True)

    # Родительская категория: null — корневая категория верхнего уровня.
    parent = models.ForeignKey(
        'self',
        verbose_name='родительская категория',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )

    # Краткое описание назначения категории (необязательно).
    description = models.TextField('описание', blank=True)

    # Порядок в фильтрах и формах (меньше — выше).
    sort_order = models.PositiveSmallIntegerField('порядок', default=0)

    # Момент создания записи в БД (для сортировки и отладки).
    created_at = models.DateTimeField('создана', auto_now_add=True)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class Region(models.Model):
    """Субъект РФ — справочник для выбора региона в объявлении и в фильтрах."""

    name = models.CharField('название', max_length=120, unique=True)

    class Meta:
        verbose_name = 'регион'
        verbose_name_plural = 'регионы'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Advertisement(models.Model):
    """
    Объявление: основная сущность доски (заголовок, текст, цена, привязка к автору и категории).
    """

    class AdType(models.TextChoices):
        SALE = 'sale', 'Продажа'
        SERVICE = 'service', 'Услуга'
        EXCHANGE = 'exchange', 'Обмен'
        AUCTION = 'auction', 'Аукцион'

    AUCTION_STEP_CHOICES = (1, 10, 100, 1000)

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PUBLISHED = 'published', 'Опубликовано'
        ARCHIVED = 'archived', 'В архиве'

    # Заголовок объявления — кратко, виден в списках и в поиске.
    title = models.CharField('заголовок', max_length=200)

    # Полный текст описания: состояние, комплектация, условия.
    description = models.TextField('описание')

    # Цена в выбранной валюте; для «договорной» цены можно договориться о null в логике форм позже.
    price = models.DecimalField('цена', max_digits=12, decimal_places=2)

    # Регион размещения — субъект РФ из справочника Region.
    region = models.ForeignKey(
        Region,
        verbose_name='регион',
        on_delete=models.PROTECT,
        related_name='advertisements',
    )

    # Тип объявления: продажа, услуга или обмен.
    ad_type = models.CharField(
        'тип объявления',
        max_length=20,
        choices=AdType.choices,
        default=AdType.SALE,
    )

    # Связь с категорией: у каждого объявления ровно одна основная категория.
    category = models.ForeignKey(
        Category,
        verbose_name='категория',
        on_delete=models.PROTECT,
        related_name='advertisements',
    )

    # Автор объявления — ссылка на кастомного пользователя проекта.
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='автор',
        on_delete=models.CASCADE,
        related_name='advertisements',
    )

    # Время создания и последнего обновления (полезно для сортировки «сначала новые»).
    created_at = models.DateTimeField('создано', auto_now_add=True)
    updated_at = models.DateTimeField('обновлено', auto_now=True)

    # Простая модерация: неактивные объявления можно скрывать из выдачи.
    is_active = models.BooleanField('активно', default=True)

    # Статус объявления для базовой логики публикации.
    status = models.CharField(
        'статус',
        max_length=20,
        choices=Status.choices,
        default=Status.PUBLISHED,
    )

    # Счетчик просмотров (инкрементируется на детальной странице).
    views_count = models.PositiveIntegerField('просмотры', default=0)

    # --- Аукцион: ad_type == AUCTION; стартовая цена = price (дублируется в start_price) ---
    start_price = models.DecimalField(
        'стартовая цена',
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    current_price = models.DecimalField(
        'текущая ставка',
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    auction_end = models.DateTimeField('окончание аукциона', null=True, blank=True)
    auction_step = models.PositiveIntegerField('шаг ставки, ₽', default=1)
    auction_finished = models.BooleanField('аукцион завершён', default=False)
    auction_winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='победитель аукциона',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_auctions',
    )

    class Meta:
        verbose_name = 'объявление'
        verbose_name_plural = 'объявления'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title

    @property
    def is_auction(self) -> bool:
        return self.ad_type == self.AdType.AUCTION

    @property
    def display_price(self):
        """Цена для отображения: текущая ставка или обычная цена."""
        if self.is_auction and self.current_price is not None:
            return self.current_price
        return self.price

    @property
    def auction_base_price(self):
        """Стартовая цена аукциона (равна полю price при создании)."""
        if self.start_price is not None:
            return self.start_price
        return self.price


class UserNotification(models.Model):
    """In-app уведомление пользователя (победа в аукционе и др.)."""

    class NotificationType(models.TextChoices):
        AUCTION_WON = 'auction_won', 'Победа в аукционе'
        AUCTION_ENDED = 'auction_ended', 'Аукцион завершён'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='получатель',
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    advertisement = models.ForeignKey(
        'Advertisement',
        verbose_name='объявление',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
    )
    notification_type = models.CharField(
        'тип',
        max_length=32,
        choices=NotificationType.choices,
    )
    title = models.CharField('заголовок', max_length=200)
    message = models.TextField('текст')
    is_read = models.BooleanField('прочитано', default=False)
    created_at = models.DateTimeField('создано', auto_now_add=True)

    class Meta:
        verbose_name = 'уведомление'
        verbose_name_plural = 'уведомления'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user}: {self.title}'


class Bid(models.Model):
    """Ставка на аукционное объявление."""

    advertisement = models.ForeignKey(
        Advertisement,
        verbose_name='объявление',
        on_delete=models.CASCADE,
        related_name='bids',
    )
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='участник',
        on_delete=models.CASCADE,
        related_name='bids',
    )
    amount = models.DecimalField('сумма ставки', max_digits=12, decimal_places=2)
    created_at = models.DateTimeField('создана', auto_now_add=True)

    class Meta:
        verbose_name = 'ставка'
        verbose_name_plural = 'ставки'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.bidder}: {self.amount} ₽'


class Photo(models.Model):
    """
    Отдельное изображение, привязанное к объявлению.

    Несколько записей на одно объявление = несколько фотографий (до 10 — проверка в формах позже).
    """

    # Объявление, к которому относится снимок.
    advertisement = models.ForeignKey(
        Advertisement,
        verbose_name='объявление',
        on_delete=models.CASCADE,
        related_name='photos',
    )

    # Файл изображения; upload_to раскладывает файлы по дате, чтобы не хранить всё в одной папке.
    image = models.ImageField('файл изображения', upload_to='ads/%Y/%m/')

    # Порядок отображения в карточке (0 — первая фотография в галерее).
    order = models.PositiveSmallIntegerField('порядок', default=0)

    # Когда файл был загружен (для отладки и очистки «осиротевших» файлов).
    uploaded_at = models.DateTimeField('загружено', auto_now_add=True)

    class Meta:
        verbose_name = 'изображение объявления'
        verbose_name_plural = 'изображения объявлений'
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return f'Фото #{self.order} к «{self.advertisement.title}»'


class Favorite(models.Model):
    """Избранное объявление пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='пользователь',
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    advertisement = models.ForeignKey(
        Advertisement,
        verbose_name='объявление',
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )
    created_at = models.DateTimeField('добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'advertisement'],
                name='unique_user_ad_favorite',
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} -> {self.advertisement}'


class AdView(models.Model):
    """
    История просмотров объявления.

    Для авторизованных — по user; для гостей — по session_key.
    Счётчик views_count на Advertisement обновляется отдельно на детальной странице.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='пользователь',
        on_delete=models.CASCADE,
        related_name='ad_views',
        null=True,
        blank=True,
    )
    advertisement = models.ForeignKey(
        Advertisement,
        verbose_name='объявление',
        on_delete=models.CASCADE,
        related_name='view_history',
    )
    session_key = models.CharField('ключ сессии', max_length=40, blank=True)
    viewed_at = models.DateTimeField('просмотрено', auto_now_add=True)

    class Meta:
        verbose_name = 'просмотр объявления'
        verbose_name_plural = 'история просмотров'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['user', '-viewed_at']),
            models.Index(fields=['session_key', '-viewed_at']),
        ]

    def __str__(self) -> str:
        who = self.user.username if self.user_id else self.session_key[:8]
        return f'{who} → {self.advertisement.title}'
