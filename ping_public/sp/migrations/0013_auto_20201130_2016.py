# Generated by Django 3.1 on 2020-11-30 20:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sp', '0012_auto_20201130_2016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attribute',
            name='query_parameters',
            field=models.ManyToManyField(blank=True, to='sp.Attribute'),
        ),
    ]