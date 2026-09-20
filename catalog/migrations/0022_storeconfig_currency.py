# Generated manually for StoreConfig.currency

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0021_telegramnotificationsettings_telegramsubscriber_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='storeconfig',
            name='currency',
            field=models.CharField(
                choices=[
                    ('сум', 'сум'),
                    ('UZS', 'UZS'),
                    ('USD', 'USD'),
                    ('EUR', 'EUR'),
                    ('RUB', 'RUB'),
                ],
                default='сум',
                help_text='Отображается рядом с ценами товаров на сайте и в админке',
                max_length=8,
                verbose_name='Валюта',
            ),
        ),
    ]
