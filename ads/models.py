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

    # Момент создания записи в БД (для сортировки и отладки).
    created_at = models.DateTimeField('создана', auto_now_add=True)

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Advertisement(models.Model):
    """
    Объявление: основная сущность доски (заголовок, текст, цена, привязка к автору и категории).
    """

    class AdType(models.TextChoices):
        # Продажа товара.
        SALE = 'sale', 'Продажа'
        # Услуга (работа, ремонт, обучение и т.д.).
        SERVICE = 'service', 'Услуга'
        # Обмен (бартер).
        EXCHANGE = 'exchange', 'Обмен'

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

    # Регион / город размещения — строкой, чтобы не усложнять справочниками на первом этапе.
    region = models.CharField('регион', max_length=120)

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

    class Meta:
        verbose_name = 'объявление'
        verbose_name_plural = 'объявления'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title


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
