# Generated by Django 4.2.5 on 2023-09-26 00:50

from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('user_id', models.AutoField(primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=50, unique=True)),
                ('username', models.CharField(max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
            ],
            options={
                'db_table': 'users',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department_name', models.CharField(max_length=255)),
                ('geo', django.contrib.gis.db.models.fields.MultiPolygonField(null=True, srid=4326)),
                ('create_on', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'departments',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Municipality',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('municipality_name', models.CharField(max_length=255)),
                ('geo', django.contrib.gis.db.models.fields.MultiPolygonField(null=True, srid=4326)),
                ('create_on', models.DateTimeField(auto_now_add=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.department')),
            ],
            options={
                'db_table': 'municipalities',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Province',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('province_name', models.CharField(max_length=255)),
                ('geo', django.contrib.gis.db.models.fields.MultiPolygonField(null=True, srid=4326)),
                ('create_on', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'provinces',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Quarter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quarter_name', models.CharField(max_length=100)),
                ('geo', django.contrib.gis.db.models.fields.MultiPolygonField(null=True, srid=4326)),
                ('create_on', models.DateTimeField(auto_now_add=True)),
                ('municipality', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.municipality')),
            ],
            options={
                'db_table': 'quarters',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TypeDamage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('damage_type_label', models.CharField(max_length=100)),
                ('create_on', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'type_damages',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='TypeRisk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('risk_type_label', models.CharField(max_length=60)),
                ('create_on', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'type_risks',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_value', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'roles',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='RiskArea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area_name', models.CharField(max_length=255)),
                ('geo', django.contrib.gis.db.models.fields.MultiPointField(srid=4326)),
                ('create_on', models.DateTimeField(auto_now_add=True)),
                ('municipality', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.municipality')),
                ('quarter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.quarter')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'risk_areas',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Risk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('risk_label', models.CharField(max_length=100)),
                ('area_affected', models.FloatField()),
                ('geo', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
                ('create_on', models.DateTimeField(auto_now_add=True)),
                ('type_risk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.typerisk')),
            ],
            options={
                'db_table': 'risks',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='HistoricalData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_label', models.CharField(max_length=100)),
                ('year_declared', models.IntegerField(default=0)),
                ('families_affected', models.IntegerField(default=0)),
                ('municipality', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.municipality')),
                ('quarter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.quarter')),
                ('type_risk', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.typerisk')),
            ],
            options={
                'db_table': 'historical_data',
                'managed': True,
            },
        ),
        migrations.AddField(
            model_name='department',
            name='province',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.province'),
        ),
        migrations.CreateModel(
            name='Damage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('severity', models.PositiveSmallIntegerField(choices=[(1, 'Faible'), (2, 'Moyen'), (3, 'Elevé'), (4, 'Extrême')], default=1)),
                ('number_families_affected', models.IntegerField(default=0)),
                ('cost_estimation', models.IntegerField(default=0)),
                ('create_on', models.DateTimeField(auto_now_add=True)),
                ('type_damage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.typedamage')),
            ],
            options={
                'db_table': 'damages',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='Building',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('building_label', models.CharField(null=True)),
                ('building_state', models.PositiveSmallIntegerField(choices=[(1, 'Inondable'), (2, 'Explosion'), (3, 'Tout'), (4, 'Aucun')], default=4)),
                ('building_area', models.FloatField()),
                ('geo', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
                ('municipality', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.municipality')),
                ('quarter', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.quarter')),
            ],
            options={
                'db_table': 'buildings',
                'managed': True,
            },
        ),
        migrations.AddField(
            model_name='appuser',
            name='municipality',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.municipality'),
        ),
        migrations.AddField(
            model_name='appuser',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.userrole'),
        ),
        migrations.AddField(
            model_name='appuser',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
    ]