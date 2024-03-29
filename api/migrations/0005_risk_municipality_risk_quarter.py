# Generated by Django 4.2.5 on 2023-09-28 03:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_risk_area_affected'),
    ]

    operations = [
        migrations.AddField(
            model_name='risk',
            name='municipality',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.municipality'),
        ),
        migrations.AddField(
            model_name='risk',
            name='quarter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.quarter'),
        ),
    ]
