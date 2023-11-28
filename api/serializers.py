from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from .models import *
from rest_framework_gis.serializers import GeoFeatureModelSerializer


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = '__all__'


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileUpload
        fields = '__all__'


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    ##
    def check_user(self, clean_data):
        user = authenticate(username=clean_data['email'], password=clean_data['password'])
        if not user:
            return False
        return user


class ProvinceSerializer(serializers.ModelSerializer):
    file = FileUploadSerializer()

    class Meta:
        model = Province
        fields = ['id', 'province_name', 'code_province', 'geo', 'file', 'create_on']


class ProvinceDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ['id', 'province_name']


class ProvinceCreateSerializer(GeoFeatureModelSerializer):
    file_field = serializers.FileField(max_length=None, use_url=True)

    class Meta:
        model = Province
        geo_field = 'geo'
        fields = ['file_field']


class DepartmentSerializer(serializers.ModelSerializer):
    province = ProvinceSerializer()
    file = FileUploadSerializer()

    class Meta:
        model = Department
        fields = ['id', 'department_name', 'file', 'create_on', 'geo', 'province']


class DepartmentDropdownSerializer(serializers.ModelSerializer):
    # province = ProvinceDropdownSerializer()

    class Meta:
        model = Department
        fields = ['id', 'department_name', 'province']


class DepartmentCreateSerializer(GeoFeatureModelSerializer):
    file_field = serializers.FileField(max_length=None, use_url=True)

    class Meta:
        model = Department
        geo_field = 'geo'
        fields = ['file_field', 'province']


class MunicipalityCreateSerializer(GeoFeatureModelSerializer):
    file_field = serializers.FileField(max_length=None, use_url=True)

    class Meta:
        model = Municipality
        geo_field = 'geo'
        fields = ['file_field', 'department']


class MunicipalitySerializer(serializers.ModelSerializer):
    file = FileUploadSerializer()
    department = DepartmentSerializer()

    class Meta:
        model = Municipality
        fields = ['id', 'municipality_name', 'department', 'file', 'create_on', 'geo']


class MunicipalityDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        fields = ['id', 'municipality_name', 'department']


class QuarterSerializer(serializers.ModelSerializer):
    file = FileUploadSerializer()
    municipality = MunicipalitySerializer()

    class Meta:
        model = Quarter
        fields = ['id', 'municipality', 'quarter_name', 'file', 'create_on', 'geo']


class QuarterCreateSerializer(GeoFeatureModelSerializer):
    file_field = serializers.FileField(max_length=None, use_url=True)

    class Meta:
        model = Quarter
        geo_field = 'geo'
        fields = ['file_field', 'municipality']


class AppUserSerializer(serializers.ModelSerializer):
    municipality = MunicipalityDropdownSerializer()
    role = UserRoleSerializer()

    class Meta:
        model = AppUser
        fields = ['user_id', 'username', 'email', 'password', 'is_staff', 'is_active', 'municipality', 'role']


class AppUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppUser
        fields = ['username', 'email', 'is_active', 'municipality', 'role']


class TypeRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeRisk
        fields = '__all__'


class RiskSerializer(serializers.ModelSerializer):
    type_risk = TypeRiskSerializer()
    municipality = MunicipalitySerializer()
    quarter = QuarterSerializer()

    class Meta:
        model = Risk
        fields = ['id', 'risk_label', 'type_risk', 'municipality', 'quarter', 'geo', 'create_on']


class RiskCreateSerializer(GeoFeatureModelSerializer):
    file_field = serializers.FileField(max_length=None, use_url=True)

    # type_risk = TypeRiskSerializer()

    class Meta:
        model = Risk
        geo_field = 'geo'
        fields = ['file_field', 'risk_label', 'type_risk']


class BuildingCreateSerializer(GeoFeatureModelSerializer):
    file_field = serializers.FileField(max_length=None, use_url=True)

    # type_risk = TypeRiskSerializer()

    class Meta:
        model = Building
        geo_field = 'geo'
        fields = ['file_field', 'building_label', 'building_state']


class BuildingSerializer(serializers.ModelSerializer):
    municipality = MunicipalitySerializer()
    quarter = QuarterSerializer()

    # type_risk = TypeRiskSerializer()

    class Meta:
        model = Building
        fields = ['id', 'building_label', 'municipality', 'quarter', 'building_state', 'file', 'building_area', 'geo']


class StationCreateSerializer(GeoFeatureModelSerializer):
    file_field = serializers.FileField(max_length=None, use_url=True)

    # type_risk = TypeRiskSerializer()

    class Meta:
        model = GasStation
        geo_field = 'geo'
        fields = ['file_field']


class StationSerializer(serializers.ModelSerializer):
    municipality = MunicipalitySerializer()
    quarter = QuarterSerializer()

    # type_risk = TypeRiskSerializer()

    class Meta:
        model = GasStation
        fields = ['id', 'name_station', 'municipality', 'quarter', 'create_on', 'geo']


class RoadCreateSerializer(GeoFeatureModelSerializer):
    file_field = serializers.FileField(max_length=None, use_url=True)

    # type_risk = TypeRiskSerializer()

    class Meta:
        model = Road
        geo_field = 'geo'
        fields = ['file_field']


class RoadSerializer(serializers.ModelSerializer):
    # type_risk = TypeRiskSerializer()

    class Meta:
        model = Road
        fields = ['id', 'road_name', 'road_distance', 'create_on', 'geo']


class RiskAreaSerializer(serializers.ModelSerializer):
    municipality = MunicipalityDropdownSerializer()
    # quarter = QuarterSerializer()
    type_risk = TypeRiskSerializer()
    # user = AppUserSerializer()

    class Meta:
        model = RiskArea
        fields = ['id', 'area_name', 'municipality', 'file', 'image_uploaded', 'type_risk', 'create_on', 'geo']


class RiskAreaCreateSerializer(GeoFeatureModelSerializer):

    class Meta:
        model = RiskArea
        geo_field = 'geo'
        fields = ['area_name', 'municipality', 'quarter', 'user', 'create_on']
