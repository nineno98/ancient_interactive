# Generated by Django 4.2.18 on 2025-02-09 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('roman_map', '0011_remove_custompolygon_created_by_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AncientPlaces',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('modern_name', models.CharField(max_length=255)),
                ('ancient_name', models.CharField(max_length=255)),
                ('coordinates', models.CharField(max_length=100)),
            ],
        ),
    ]
