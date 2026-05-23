import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0010_seed_categories'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'notification_type',
                    models.CharField(
                        choices=[
                            ('auction_won', 'Победа в аукционе'),
                            ('auction_ended', 'Аукцион завершён'),
                        ],
                        max_length=32,
                        verbose_name='тип',
                    ),
                ),
                ('title', models.CharField(max_length=200, verbose_name='заголовок')),
                ('message', models.TextField(verbose_name='текст')),
                ('is_read', models.BooleanField(default=False, verbose_name='прочитано')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создано')),
                (
                    'advertisement',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='notifications',
                        to='ads.advertisement',
                        verbose_name='объявление',
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='notifications',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='получатель',
                    ),
                ),
            ],
            options={
                'verbose_name': 'уведомление',
                'verbose_name_plural': 'уведомления',
                'ordering': ['-created_at'],
            },
        ),
    ]
