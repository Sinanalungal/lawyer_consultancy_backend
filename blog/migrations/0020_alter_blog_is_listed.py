# Generated by Django 4.0 on 2024-08-02 21:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0019_rename_checked_blog_is_listed_remove_blog_valid_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blog',
            name='is_listed',
            field=models.BooleanField(default=True),
        ),
    ]
