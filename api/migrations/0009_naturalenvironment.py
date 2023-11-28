# Generated by Django 4.2.5 on 2023-10-16 21:10

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_road'),
    ]

    operations = [
        migrations.CreateModel(
            name='NaturalEnvironment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
                ('river_name', models.CharField(max_length=100, null=True)),
                ('municipality', models.FloatField(default=0.0)),
                ('geo', django.contrib.gis.db.models.fields.MultiLineStringField(srid=4326)),
                ('create_on', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'natural_environment',
                'managed': True,
            },
        ),
    ]