"""Идемпотентная замена категорий на актуальный справочник."""

from django.db import migrations

CANONICAL_CATEGORIES = [
    ('nedvizhimost', 'Недвижимость', 1),
    ('transport', 'Транспорт', 2),
    ('elektronika', 'Электроника', 3),
    ('bytovaya-tehnika', 'Бытовая техника', 4),
    ('mebel-i-interer', 'Мебель и интерьер', 5),
    ('odezhda-obuv-aksessuary', 'Одежда, обувь и аксессуары', 6),
    ('dlya-doma-i-dachi', 'Для дома и дачи', 7),
    ('zhivotnye', 'Животные', 8),
    ('uslugi', 'Услуги', 9),
    ('rabota', 'Работа', 10),
    ('hobi-i-sport', 'Хобби и спорт', 11),
    ('krasota-i-zdorovie', 'Красота и здоровье', 12),
    ('detskie-tovary', 'Детские товары', 13),
    ('besplatno', 'Бесплатно', 14),
    ('stroitelstvo-i-remont', 'Строительство и ремонт', 15),
]

CANONICAL_SLUGS = {slug for slug, _, _ in CANONICAL_CATEGORIES}

# Старые названия/слаги → новый slug
LEGACY_MAP = {
    'вещи': 'dlya-doma-i-dachi',
    'veshi': 'dlya-doma-i-dachi',
    'things': 'dlya-doma-i-dachi',
    'мусор': 'besplatno',
    'musor': 'besplatno',
    'trash': 'besplatno',
    'недвижка': 'nedvizhimost',
    'nedvizhka': 'nedvizhimost',
    'недвижимость': 'nedvizhimost',
    'realty': 'nedvizhimost',
    'электроника': 'elektronika',
    'transport': 'transport',
    'услуги': 'uslugi',
    'uslugi': 'uslugi',
}


def seed_categories(apps, schema_editor):
    Category = apps.get_model('ads', 'Category')
    Advertisement = apps.get_model('ads', 'Advertisement')

    for slug, name, sort_order in CANONICAL_CATEGORIES:
        Category.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'sort_order': sort_order,
                'parent': None,
                'description': '',
            },
        )

    default_category = Category.objects.get(slug='dlya-doma-i-dachi')

    for category in list(Category.objects.exclude(slug__in=CANONICAL_SLUGS)):
        key_name = category.name.lower().strip()
        key_slug = category.slug.lower().strip()
        target_slug = LEGACY_MAP.get(key_name) or LEGACY_MAP.get(key_slug)
        if target_slug:
            target = Category.objects.get(slug=target_slug)
        else:
            target = default_category
        Advertisement.objects.filter(category_id=category.pk).update(category=target)
        category.delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0009_category_sort_order'),
    ]

    operations = [
        migrations.RunPython(seed_categories, noop_reverse),
    ]
