# Generated by Django 5.1.5 on 2025-06-03 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='driver',
            name='trucks',
            field=models.ManyToManyField(blank=True, to='core.truck'),
        ),
    ]
