# Миграция: справочник регионов РФ и замена текстового поля region на ForeignKey.

from django.db import migrations, models
import django.db.models.deletion


def load_regions(apps, schema_editor):
    Region = apps.get_model('ads', 'Region')
    from ads.regions_data import RUSSIAN_REGIONS

    for name in RUSSIAN_REGIONS:
        Region.objects.get_or_create(name=name)


def migrate_advertisement_regions(apps, schema_editor):
    """Перенос старых текстовых значений region в справочник."""
    Region = apps.get_model('ads', 'Region')
    Advertisement = apps.get_model('ads', 'Advertisement')
    from ads.regions_data import REGION_ALIASES

    default = Region.objects.filter(name='Москва').first()
    if default is None:
        default = Region.objects.first()

    for ad in Advertisement.objects.all():
        old_text = (ad.region_old or '').strip()
        region = None
        if old_text:
            region = Region.objects.filter(name=old_text).first()
            if region is None:
                region = Region.objects.filter(name__iexact=old_text).first()
            if region is None:
                alias = REGION_ALIASES.get(old_text.lower())
                if alias:
                    region = Region.objects.filter(name=alias).first()
            if region is None:
                lower = old_text.lower()
                for candidate in Region.objects.all():
                    if lower in candidate.name.lower() or candidate.name.lower() in lower:
                        region = candidate
                        break
        ad.region_id = (region or default).pk
        ad.save(update_fields=['region_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0004_adview'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True, verbose_name='название')),
            ],
            options={
                'verbose_name': 'регион',
                'verbose_name_plural': 'регионы',
                'ordering': ['name'],
            },
        ),
        migrations.RunPython(load_regions, migrations.RunPython.noop),
        migrations.RenameField(
            model_name='advertisement',
            old_name='region',
            new_name='region_old',
        ),
        migrations.AddField(
            model_name='advertisement',
            name='region',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='advertisements',
                to='ads.region',
                verbose_name='регион',
            ),
        ),
        migrations.RunPython(migrate_advertisement_regions, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='advertisement',
            name='region',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='advertisements',
                to='ads.region',
                verbose_name='регион',
            ),
        ),
        migrations.RemoveField(
            model_name='advertisement',
            name='region_old',
        ),
    ]
