# Generated by Django 4.0 on 2024-08-12 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_language_remove_lawyerprofile_document_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lawyerprofile',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='lawyerprofile',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='lawyerprofile',
            name='postal_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='lawyerprofile',
            name='state',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
