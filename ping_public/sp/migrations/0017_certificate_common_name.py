# Generated by Django 3.1 on 2021-01-06 23:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp', '0016_auto_20210102_0125'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificate',
            name='common_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]