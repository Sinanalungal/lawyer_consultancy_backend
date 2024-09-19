# Generated by Django 5.1 on 2024-09-19 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0022_remove_blog_is_listed_blog_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Listed', 'Listed'), ('Blocked', 'Blocked')], default='Pending', max_length=10),
        ),
    ]
