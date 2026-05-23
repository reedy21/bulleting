# Generated manually for Sprint 6 auction fields

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ads', '0005_region'),
    ]

    operations = [
        migrations.AddField(
            model_name='advertisement',
            name='auction_end',
            field=models.DateTimeField(blank=True, null=True, verbose_name='окончание аукциона'),
        ),
        migrations.AddField(
            model_name='advertisement',
            name='auction_finished',
            field=models.BooleanField(default=False, verbose_name='аукцион завершён'),
        ),
        migrations.AddField(
            model_name='advertisement',
            name='current_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name='текущая ставка',
            ),
        ),
        migrations.AddField(
            model_name='advertisement',
            name='is_auction',
            field=models.BooleanField(default=False, verbose_name='аукцион'),
        ),
        migrations.AddField(
            model_name='advertisement',
            name='start_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name='стартовая цена',
            ),
        ),
        migrations.AddField(
            model_name='advertisement',
            name='auction_winner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='won_auctions',
                to=settings.AUTH_USER_MODEL,
                verbose_name='победитель аукциона',
            ),
        ),
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'amount',
                    models.DecimalField(decimal_places=2, max_digits=12, verbose_name='сумма ставки'),
                ),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создана')),
                (
                    'advertisement',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='bids',
                        to='ads.advertisement',
                        verbose_name='объявление',
                    ),
                ),
                (
                    'bidder',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='bids',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='участник',
                    ),
                ),
            ],
            options={
                'verbose_name': 'ставка',
                'verbose_name_plural': 'ставки',
                'ordering': ['-created_at'],
            },
        ),
    ]
