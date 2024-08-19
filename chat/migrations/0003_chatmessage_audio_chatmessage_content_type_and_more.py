# Generated by Django 4.0 on 2024-08-19 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_thread_is_listed'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='audio',
            field=models.FileField(blank=True, null=True, upload_to='audio/'),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='content_type',
            field=models.CharField(choices=[('text', 'Text'), ('audio', 'Audio'), ('video', 'Video'), ('image', 'Image')], default='text', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/'),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='video',
            field=models.FileField(blank=True, null=True, upload_to='video/'),
        ),
        migrations.AlterField(
            model_name='chatmessage',
            name='message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
