# Generated manually for Sprint 3 updates.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ads', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='advertisement',
            name='status',
            field=models.CharField(
                choices=[('draft', 'Черновик'), ('published', 'Опубликовано'), ('archived', 'В архиве')],
                default='published',
                max_length=20,
                verbose_name='статус',
            ),
        ),
        migrations.AddField(
            model_name='advertisement',
            name='views_count',
            field=models.PositiveIntegerField(default=0, verbose_name='просмотры'),
        ),
        migrations.RenameModel(
            old_name='AdvertisementImage',
            new_name='Photo',
        ),
        migrations.AlterField(
            model_name='photo',
            name='advertisement',
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name='photos',
                to='ads.advertisement',
                verbose_name='объявление',
            ),
        ),
    ]
