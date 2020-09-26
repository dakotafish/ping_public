# Generated by Django 3.1 on 2020-09-05 02:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Destination',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('entity_id', models.CharField(max_length=100)),
                ('virtual_server_id', models.CharField(max_length=100)),
                ('is_encrypted', models.BooleanField(default=False)),
                ('signature_validation', models.CharField(choices=[('RESPONSE', 'Validate Signature in SAML Response'), ('ASSERTION', 'Validate Signature in SAML Assertion')], default='RESPONSE', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='RelayState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url_pattern', models.CharField(max_length=200)),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sp.destination')),
            ],
        ),
        migrations.AddField(
            model_name='destination',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sp.entity'),
        ),
        migrations.CreateModel(
            name='Certificate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('certificate', models.TextField()),
                ('certificate_info', models.TextField()),
                ('expiration_date', models.DateTimeField()),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sp.entity')),
            ],
        ),
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attribute_name', models.CharField(max_length=100)),
                ('attribute_value', models.TextField()),
                ('attribute_type', models.CharField(choices=[('ASSERTION', 'Take value as is from the assertion.'), ('ALTER', 'Take value from the assertion and alter it.'), ('QUERY', 'Use values from the assertion to run a query.')], default='ASSERTION', max_length=100)),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sp.destination')),
            ],
        ),
    ]
