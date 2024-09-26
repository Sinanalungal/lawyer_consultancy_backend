# Generated by Django 5.1 on 2024-09-25 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notifications',
            options={'ordering': ['-notify_time'], 'verbose_name': 'Notification', 'verbose_name_plural': 'Notifications'},
        ),
        migrations.RemoveField(
            model_name='notifications',
            name='created_at',
        ),
        migrations.AddField(
            model_name='notifications',
            name='notify_time',
            field=models.DateTimeField(default='2024-10-01T14:30:00'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notifications',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending', max_length=10),
        ),
    ]
