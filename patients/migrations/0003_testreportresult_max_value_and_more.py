# Generated by Django 5.2 on 2025-04-10 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0002_patient_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='testreportresult',
            name='max_value',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='testreportresult',
            name='min_value',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='testreportresult',
            name='unit',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
