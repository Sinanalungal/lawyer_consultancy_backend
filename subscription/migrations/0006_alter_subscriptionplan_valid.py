# Generated by Django 5.0.4 on 2024-05-28 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0005_subscriptionplan_valid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscriptionplan',
            name='valid',
            field=models.BooleanField(default=False),
        ),
    ]
