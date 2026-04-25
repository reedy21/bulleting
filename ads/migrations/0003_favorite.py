from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('ads', '0002_advertisement_status_views_and_photo_rename'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='добавлено')),
                (
                    'advertisement',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='favorited_by',
                        to='ads.advertisement',
                        verbose_name='объявление',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name='favorites',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='пользователь',
                    ),
                ),
            ],
            options={
                'verbose_name': 'избранное',
                'verbose_name_plural': 'избранное',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='favorite',
            constraint=models.UniqueConstraint(fields=('user', 'advertisement'), name='unique_user_ad_favorite'),
        ),
    ]
