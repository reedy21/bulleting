from django.db import migrations, models


def forwards_auction_type(apps, schema_editor):
    Advertisement = apps.get_model('ads', 'Advertisement')
    Advertisement.objects.filter(is_auction=True).update(ad_type='auction')


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0007_auction_step'),
    ]

    operations = [
        migrations.RunPython(forwards_auction_type, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='advertisement',
            name='is_auction',
        ),
        migrations.AlterField(
            model_name='advertisement',
            name='ad_type',
            field=models.CharField(
                choices=[
                    ('sale', 'Продажа'),
                    ('service', 'Услуга'),
                    ('exchange', 'Обмен'),
                    ('auction', 'Аукцион'),
                ],
                default='sale',
                max_length=20,
                verbose_name='тип объявления',
            ),
        ),
    ]
