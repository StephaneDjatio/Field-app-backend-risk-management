# Generated by Django 4.2.5 on 2023-09-30 10:11

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_risk_municipality_risk_quarter'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaldata',
            name='geo',
            field=django.contrib.gis.db.models.fields.MultiPointField(null=True, srid=4326),
        ),
    ]