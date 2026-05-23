from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0008_auction_ad_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='sort_order',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='порядок'),
        ),
        migrations.AlterModelOptions(
            name='category',
            options={
                'ordering': ['sort_order', 'name'],
                'verbose_name': 'категория',
                'verbose_name_plural': 'категории',
            },
        ),
    ]
