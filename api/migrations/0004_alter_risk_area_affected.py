# Generated by Django 4.2.5 on 2023-09-28 01:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_province_code_province'),
    ]

    operations = [
        migrations.AlterField(
            model_name='risk',
            name='area_affected',
            field=models.FloatField(default=0),
        ),
    ]