# Generated by Django 5.1.3 on 2025-04-11 20:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0009_property_competitor_density'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='property',
            name='success_index',
        ),
    ]
