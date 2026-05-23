from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0006_auction'),
    ]

    operations = [
        migrations.AddField(
            model_name='advertisement',
            name='auction_step',
            field=models.PositiveIntegerField(default=1, verbose_name='шаг ставки, ₽'),
        ),
    ]
