# Generated by Django 4.0 on 2024-06-14 13:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_alter_customuser_departments_alter_customuser_groups_and_more'),
        ('blog', '0017_report_note'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='report',
            unique_together={('user', 'blog')},
        ),
    ]
