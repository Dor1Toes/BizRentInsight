# Generated by Django 5.1.3 on 2025-04-11 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0008_property_adjusted_price_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='competitor_density',
            field=models.IntegerField(default=0),
        ),
    ]
