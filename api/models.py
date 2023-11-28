from django.contrib.gis.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin


# Create your models here.

class FileUpload(models.Model):
    file = models.FileField(upload_to='%Y/%m/%d')
    filename = models.CharField(max_length=255)
    srs_wkt = models.CharField(max_length=255)
    geom_type = models.CharField(max_length=55)

    class Meta:
        managed = True
        db_table = 'uploadedFiles'

    def __str__(self):
        return self.file


class Province(models.Model):
    province_name = models.CharField(max_length=255)
    code_province = models.CharField(max_length=20, null=True)
    file = models.ForeignKey(FileUpload, on_delete=models.CASCADE, null=True)
    geo = models.MultiPolygonField(srid=4326, null=True)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'provinces'

    def __str__(self):
        return self.province_name


class Department(models.Model):
    department_name = models.CharField(max_length=255)
    province = models.ForeignKey(Province, on_delete=models.CASCADE)
    file = models.ForeignKey(FileUpload, on_delete=models.CASCADE, null=True)
    geo = models.MultiPolygonField(srid=4326, null=True)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'departments'

    def __str__(self):
        return self.department_name


class Municipality(models.Model):
    municipality_name = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    file = models.ForeignKey(FileUpload, on_delete=models.CASCADE, null=True)
    geo = models.MultiPolygonField(srid=4326, null=True)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'municipalities'

    def __str__(self):
        return self.municipality_name


class Quarter(models.Model):
    quarter_name = models.CharField(max_length=100)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    file = models.ForeignKey(FileUpload, on_delete=models.CASCADE, null=True)
    geo = models.MultiPolygonField(srid=4326, null=True)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'quarters'

    def __str__(self):
        return self.quarter_name


class UserRole(models.Model):
    role_value = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = 'roles'

    def __str__(self):
        return self.role_value


class AppUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('An email is required.')
        if not password:
            raise ValueError('A password is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, municipality, role, password=None, **extra_fields):
        if not email:
            raise ValueError('An email is required.')
        if not password:
            raise ValueError('A password is required.')

        # Check if Municipality is provided and retrieve the Municipality instance if it is
        if municipality:
            try:
                municipality_instance = Municipality.objects.get(pk=municipality)
            except Municipality.DoesNotExist:
                raise ValueError('Invalid city ID')
            extra_fields['municipality'] = municipality_instance

        if role:
            try:
                role_instance = UserRole.objects.get(pk=role)
            except UserRole.DoesNotExist:
                raise ValueError('Invalid city ID')
            extra_fields['role'] = role_instance

        user = self.create_user(email, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class AppUser(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=50, unique=True)
    username = models.CharField(max_length=50)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True)
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateField(auto_now_add=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'role', 'municipality']
    objects = AppUserManager()

    class Meta:
        managed = True
        db_table = 'users'

    def __str__(self):
        return self.username


class TypeRisk(models.Model):
    risk_type_label = models.CharField(max_length=60)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'type_risks'

    def __str__(self):
        return self.risk_type_label


class RiskArea(models.Model):
    area_name = models.CharField(max_length=255)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
    # quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE, null=True)
    type_risk = models.ForeignKey(TypeRisk, on_delete=models.CASCADE, null=True)
    # user = models.ForeignKey(AppUser, on_delete=models.CASCADE, null=True)
    file = models.FileField(upload_to='pictures/%Y/%m/%d', null=True)
    image_uploaded = models.BooleanField(default=False)
    geo = models.MultiPointField(srid=4326)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'risk_areas'

    def __str__(self):
        return self.area_name


class TypeDamage(models.Model):
    damage_type_label = models.CharField(max_length=100)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'type_damages'

    def __str__(self):
        return self.damage_type_label


class Damage(models.Model):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    EXTREME = 4
    STATUS = (
        (LOW, 'Faible'),
        (MEDIUM, 'Moyen'),
        (HIGH, 'Elevé'),
        (EXTREME, 'Extrême'),
    )
    type_damage = models.ForeignKey(TypeDamage, on_delete=models.CASCADE)
    severity = models.PositiveSmallIntegerField(choices=STATUS, default=LOW)
    number_families_affected = models.IntegerField(default=0)
    cost_estimation = models.IntegerField(default=0)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'damages'

    def __str__(self):
        return self.type_name


class Risk(models.Model):
    risk_label = models.CharField(max_length=100)
    type_risk = models.ForeignKey(TypeRisk, on_delete=models.CASCADE)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True)
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE, null=True)
    file = models.ForeignKey(FileUpload, on_delete=models.CASCADE, null=True)
    area_affected = models.FloatField(default=0)
    geo = models.MultiPolygonField(srid=4326)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'risks'

    def __str__(self):
        return self.risk_label


class Building(models.Model):
    FLOOD = 1
    EXPLOSION = 2
    BOTH = 3
    NONE = 4
    STATUS = (
        (FLOOD, 'Inondable'),
        (EXPLOSION, 'Explosion'),
        (BOTH, 'Tout'),
        (NONE, 'Aucun'),
    )
    building_label = models.CharField(null=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True)
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE, null=True)
    building_state = models.PositiveSmallIntegerField(choices=STATUS, default=NONE)
    file = models.ForeignKey(FileUpload, on_delete=models.CASCADE, null=True)
    building_area = models.FloatField()
    geo = models.MultiPolygonField(srid=4326)

    class Meta:
        managed = True
        db_table = 'buildings'

    def __str__(self):
        return self.building_label


class HistoricalData(models.Model):
    data_label = models.CharField(max_length=100)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True)
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE, null=True)
    type_risk = models.ForeignKey(TypeRisk, on_delete=models.CASCADE)
    year_declared = models.IntegerField(default=0)
    families_affected = models.IntegerField(default=0)
    geo = models.MultiPointField(srid=4326, null=True)

    class Meta:
        managed = True
        db_table = 'historical_data'

    def __str__(self):
        return self.data_label


class GasStation(models.Model):
    name_station = models.CharField(max_length=100)
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, null=True)
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE, null=True)
    geo = models.MultiPointField(srid=4326)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'stations_service'

    def __str__(self):
        return self.name_station


class Road(models.Model):
    road_name = models.CharField(max_length=100, null=True)
    road_distance = models.FloatField(default=0.0)
    geo = models.MultiLineStringField(srid=4326)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'roads'

    def __str__(self):
        return self.road_name


class NaturalEnvironment(models.Model):
    name = models.CharField(max_length=100, null=True)
    river_name = models.CharField(max_length=100, null=True)
    municipality = models.FloatField(default=0.0)
    geo = models.MultiLineStringField(srid=4326)
    create_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'natural_environment'

    def __str__(self):
        return self.name
