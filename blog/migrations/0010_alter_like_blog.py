# Generated by Django 5.0.4 on 2024-05-16 10:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0009_like_like_alter_blog_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='like',
            name='blog',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='blog.blog'),
        ),
    ]
