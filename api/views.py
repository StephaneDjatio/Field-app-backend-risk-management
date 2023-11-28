import glob
import os
import shutil
import traceback
import zipfile
from datetime import datetime

from django.contrib.auth import login, logout
from django.contrib.auth.hashers import make_password
from osgeo import ogr, osr
from django.contrib.gis.geos.geometry import GEOSGeometry
from django.contrib.gis.geos.collections import MultiLineString, MultiPoint, MultiPolygon
from django.contrib.gis.geos import Point
from requests import HTTPError
from rest_framework import status, generics, permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from webRisk.settings import BASE_DIR
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .validations import validate_email, validate_password
import geopandas as gpd
from .serializers import *

# Create your views here.

out_epsg = 4326
ogr.UseExceptions()


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # Number of items per page
    page_query_param = 'page'  # The query parameter for specifying the page number
    page_size_query_param = 'page_size'  # The query parameter for specifying the page size
    max_page_size = 100  # The maximum allowed page size


def check_zip_for_extensions(zip_file_path, extensions):
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_file:
            files_in_zip = zip_file.namelist()
            files_with_extensions = [file for file in files_in_zip if any(file.endswith(ext) for ext in extensions)]

            if files_with_extensions:
                return True
            else:
                return False
    except zipfile.BadZipFile:
        print("The provided file is not a valid ZIP archive.")
    except Exception as e:
        print(f"An error occurred: {e}")


class UserRoleView(APIView):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        queryset = UserRole.objects.all()
        serializer = UserRoleSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        role_value = request.POST.get('role_value')
        UserRole.objects.create(role_value=role_value)
        return Response({'message': 'User profile created.'}, status=status.HTTP_201_CREATED)


class UserRoleUpdate(generics.UpdateAPIView):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (permissions.AllowAny,)


class UserRoleId(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, **kwargs):
        queryset = UserRole.objects.filter(pk=kwargs['id']).first()
        serializer = UserRoleSerializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AppUserView(APIView):
    queryset = AppUser.objects.all()
    serializer_class = AppUserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, **kwargs):
        if 'id' not in kwargs:
            queryset = AppUser.objects.all()
            serializer = AppUserSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = AppUser.objects.filter(pk=kwargs['id']).first()
            serializer = AppUserSerializer(queryset)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        is_active = request.POST.get('is_active')
        is_staff = request.POST.get('is_staff')
        print(is_active)
        municipality = Municipality.objects.filter(id=request.POST.get('municipality'))
        role = UserRole.objects.filter(id=request.POST.get('role'))
        AppUser.objects.create(
            email=email,
            username=username,
            password=make_password(password),
            municipality=municipality[0],
            role=role[0],
            is_active=is_active.capitalize(),
            is_staff=is_staff.capitalize()
        )
        return Response({'message': 'User created.'}, status=status.HTTP_201_CREATED)


class UserUpdate(generics.UpdateAPIView):
    queryset = AppUser.objects.all()
    serializer_class = AppUserUpdateSerializer
    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (permissions.AllowAny,)


class UserLogin(APIView):
    permission_classes = (permissions.AllowAny,)

    # authentication_classes = (TokenAuthentication,)

    ##
    def post(self, request):
        data = request.data
        print(data)
        assert validate_email(data)
        assert validate_password(data)
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.check_user(data)
            if user:
                login(request, user)
                token, created = Token.objects.get_or_create(user=user)
                new_serializer = AppUserSerializer(user)
                print(new_serializer.data)
                response = {"user": new_serializer.data, "token": token.key, "status": status.HTTP_200_OK}
                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response({"status": status.HTTP_205_RESET_CONTENT}, status=status.HTTP_205_RESET_CONTENT)
        else:
            return Response({"status": status.HTTP_303_SEE_OTHER}, status=status.HTTP_303_SEE_OTHER)


class UserLogout(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)


def checkUserEmail(request):
    email = request.POST.get('email')
    existing_user = AppUser.objects.filter(email=email).first()

    if existing_user:
        # Email is already in use
        return Response({"status": status.HTTP_303_SEE_OTHER}, status=status.HTTP_303_SEE_OTHER)
    else:
        return Response({"status": status.HTTP_200_OK}, status=status.HTTP_200_OK)


class ProvinceCreateView(APIView):
    queryset = Province.objects.all()
    serializer_class = ProvinceCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        shapefile = request.FILES.get('file_field')
        default_attributtes = ['PROVINCE', 'CHEF_PROV', 'CODE']
        if shapefile:
            # Save the uploaded file to the UploadedFile model
            new_file = FileUpload.objects.create(file=shapefile)
            file = new_file.file.path
            file_path = os.path.dirname(file)
            file_name = os.path.basename(file).split('.')[0]
            file_extract_path = os.path.join(file_path, file_name)
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(file_extract_path)

            os.remove(file)
            # we get the shapefile from the extracted zip file
            shp = glob.glob(r'{}/**/*.shp'.format(file_extract_path), recursive=True)[0]

            # using ogr to interact with the shapefile
            try:
                datasource = ogr.Open(shp)
                layer = datasource.GetLayer(0)
                shapefile_ok = True
                print('Shapefile ok')
            except Exception as e:
                traceback.print_exc()
                shapefile_ok = False
                print(f"An error occurred: {str(e)}")
                print('Bad Shapefile')

            '''
            creating array to store attribute labels of the features
            '''
            attributes = []
            layer_def = layer.GetLayerDefn()
            for i in range(layer_def.GetFieldCount()):
                field_def = layer_def.GetFieldDefn(i)
                name = field_def.GetName()
                attributes.append(name)

            print(attributes)

            contains_value = any(item in default_attributtes for item in attributes)

            if contains_value is True:

                for i in range(layer.GetFeatureCount()):
                    src_feature = layer.GetFeature(i)
                    src_geometry = src_feature.GetGeometryRef()

                    '''
                    check if there is a feature missing geometry
                    '''
                    if src_geometry is not None:
                        '''
                        Check if the source and destination spatial ref are equal before transformation
                        helps prevent coordinate reversing
                        '''
                        # if str(src_spatial_ref) != str(dst_spatial_ref):
                        #     src_geometry.Transform(coord_transform)
                        #     print('hello i am not equal')

                        geometry = GEOSGeometry(src_geometry.ExportToWkt())

                        if geometry.geom_type != 'MultiPolygon':
                            geometry = MultiPolygon(geometry)
                        province = Province(
                            province_name=src_feature.GetFieldAsString('PROVINCE'),
                            code_province=src_feature.GetFieldAsString('CODE'),
                            file=new_file,
                            geo=geometry
                        )
                        province.save()

                return Response({'message': 'Shapefile data uploaded successfully.'})
            else:
                return Response({
                    'error': 'La table attributaire de votre fichier ne contient pas les champs requis!!!',
                    'Champs requis': default_attributtes
                })
        else:
            return Response({'error': 'No Shapefile provided.'}, status=400)


class ProvinceList(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        if 'id' not in kwargs:
            provinces = Province.objects.all()
            paginator = PageNumberPagination()
            page = paginator.paginate_queryset(provinces, request)
            if page is not None:
                serializer = ProvinceSerializer(page, many=True)  # Replace with your serializer
                return Response(serializer.data, status=status.HTTP_200_OK)
            serializer = ProvinceSerializer(provinces, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            province = Province.objects.filter(pk=kwargs['id']).first()
            serializer = ProvinceSerializer(province)
            return Response(serializer.data, status=status.HTTP_200_OK)


class ProvinceDropdownList(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        provinces = Province.objects.all()
        serializer = ProvinceDropdownSerializer(provinces, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DepartmentCreateView(APIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        shapefile = request.FILES.get('file_field')
        default_attributtes = ['CODE_DGSEE', 'NOM_DEPT', 'NOM_PROV']
        if shapefile:
            # Save the uploaded file to the UploadedFile model
            new_file = FileUpload.objects.create(file=shapefile)
            file = new_file.file.path
            file_path = os.path.dirname(file)
            file_name = os.path.basename(file).split('.')[0]
            file_extract_path = os.path.join(file_path, file_name)
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(file_extract_path)

            os.remove(file)
            # we get the shapefile from the extracted zip file
            shp = glob.glob(r'{}/**/*.shp'.format(file_extract_path), recursive=True)[0]

            gdf = gpd.read_file(shp)
            my_crs = gdf.crs.to_epsg()
            print(my_crs)
            if my_crs != out_epsg:
                gdf_new = gdf.to_crs(epsg=out_epsg)
                gdf_new.to_file(os.path.abspath(os.path.join(BASE_DIR, 'media/changed_data/changed_data.shp')))
                shp = os.path.abspath(os.path.join(BASE_DIR, 'media/changed_data/changed_data.shp'))

            # using ogr to interact with the shapefile
            try:
                datasource = ogr.Open(shp)
                layer = datasource.GetLayer(0)
                shapefile_ok = True
                print('Shapefile ok')
            except Exception as e:
                traceback.print_exc()
                shapefile_ok = False
                print(f"An error occurred: {str(e)}")
                print('Bad Shapefile')

            '''
            creating array to store attribute labels of the features
            '''
            attributes = []
            layer_def = layer.GetLayerDefn()
            for i in range(layer_def.GetFieldCount()):
                field_def = layer_def.GetFieldDefn(i)
                name = field_def.GetName()
                attributes.append(name)

            print(attributes)

            contains_value = any(item in default_attributtes for item in attributes)

            if contains_value is True:
                for i in range(layer.GetFeatureCount()):
                    src_feature = layer.GetFeature(i)
                    src_geometry = src_feature.GetGeometryRef()

                    '''
                    check if there is a feature missing geometry
                    '''
                    if src_geometry is not None:
                        '''
                        Check if the source and destination spatial ref are equal before transformation
                        helps prevent coordinate reversing
                        '''
                        # if str(src_spatial_ref) != str(dst_spatial_ref):
                        #     src_geometry.Transform(coord_transform)
                        #     print('hello i am not equal')

                        geometry = GEOSGeometry(src_geometry.ExportToWkt())

                        if geometry.geom_type != 'MultiPolygon':
                            geometry = MultiPolygon(geometry)
                        filtered_province = Province.objects.filter(
                            province_name__contains=src_feature.GetFieldAsString('NOM_PROV'))
                        # print(filtered_province[0])
                        department = Department(
                            department_name=src_feature.GetFieldAsString('NOM_DEPT'),
                            province=filtered_province[0],
                            file=new_file,
                            geo=geometry
                        )
                        department.save()

                shutil.rmtree(file_extract_path)

                return Response({'message': 'Shapefile data uploaded successfully.'})
            else:
                shutil.rmtree(file_extract_path)
                return Response({
                    'error': 'La table attributaire de votre fichier ne contient pas les champs requis!!!',
                    'Champs requis': default_attributtes
                })

        else:
            return Response({'error': 'No Shapefile provided.'}, status=400)


class DepartmentList(APIView):
    pagination_class = CustomPageNumberPagination  # Apply your custom pagination class
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        if 'id' not in kwargs:
            queryset = Department.objects.all()
            serializer = DepartmentSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            department = Department.objects.filter(pk=kwargs['id']).first()
            serializer = DepartmentSerializer(department)
            return Response(serializer.data, status=status.HTTP_200_OK)


class DepartmentListForMobile(APIView):
    pagination_class = CustomPageNumberPagination  # Apply your custom pagination class
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        department = Department.objects.all()
        serializer = DepartmentDropdownSerializer(department, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DepartmentDropdownListByProvince(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        queryset = Department.objects.filter(province_id=kwargs['province_id']).all()
        serializer = DepartmentDropdownSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MunicipalityCreateView(APIView):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        shapefile = request.FILES.get('file_field')
        default_attributtes = ['COMMUNE', 'DEPARTEMEN']
        if shapefile:
            # Save the uploaded file to the UploadedFile model
            new_file = FileUpload.objects.create(file=shapefile)
            file = new_file.file.path
            file_path = os.path.dirname(file)
            file_name = os.path.basename(file).split('.')[0]
            file_extract_path = os.path.join(file_path, file_name)
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(file_extract_path)

            os.remove(file)
            # we get the shapefile from the extracted zip file
            shp = glob.glob(r'{}/**/*.shp'.format(file_extract_path), recursive=True)[0]

            gdf = gpd.read_file(shp)
            my_crs = gdf.crs.to_epsg()
            # print(my_crs)
            if my_crs != out_epsg:
                gdf_new = gdf.to_crs(epsg=out_epsg)
                gdf_new.to_file(os.path.abspath(os.path.join(BASE_DIR, 'media/changed_data/changed_data.shp')))
                shp = os.path.abspath(os.path.join(BASE_DIR, 'media/changed_data/changed_data.shp'))

            # using ogr to interact with the shapefile
            try:
                datasource = ogr.Open(shp)
                layer = datasource.GetLayer(0)
                shapefile_ok = True
                print('Shapefile ok')
            except Exception as e:
                traceback.print_exc()
                shapefile_ok = False
                print(f"An error occurred: {str(e)}")
                print('Bad Shapefile')

            '''
            creating array to store attribute labels of the features
            '''
            attributes = []
            layer_def = layer.GetLayerDefn()
            for i in range(layer_def.GetFieldCount()):
                field_def = layer_def.GetFieldDefn(i)
                name = field_def.GetName()
                attributes.append(name)

            print(attributes)

            contains_value = any(item in default_attributtes for item in attributes)

            if contains_value is True:
                for i in range(layer.GetFeatureCount()):
                    src_feature = layer.GetFeature(i)
                    src_geometry = src_feature.GetGeometryRef()

                    '''
                    check if there is a feature missing geometry
                    '''
                    if src_geometry is not None:
                        '''
                        Check if the source and destination spatial ref are equal before transformation
                        helps prevent coordinate reversing
                        '''
                        # if str(src_spatial_ref) != str(dst_spatial_ref):
                        #     src_geometry.Transform(coord_transform)
                        #     print('hello i am not equal')

                        geometry = GEOSGeometry(src_geometry.ExportToWkt())

                        if geometry.geom_type != 'MultiPolygon':
                            geometry = MultiPolygon(geometry)
                        filtered_department = Department.objects.filter(
                            department_name__contains=src_feature.GetFieldAsString('DEPARTEMEN'))
                        print(
                            f"{src_feature.GetFieldAsString('DEPARTEMEN')} -> {src_feature.GetFieldAsString('COMMUNE')}")
                        # if len(filtered_department) != 0:
                        print(filtered_department[0])
                        municipality = Municipality(
                            municipality_name=src_feature.GetFieldAsString('COMMUNE'),
                            department=filtered_department[0],
                            file=new_file,
                            geo=geometry
                        )
                        municipality.save()

                shutil.rmtree(file_extract_path)

                return Response({'message': 'Shapefile data uploaded successfully.'})
            else:
                shutil.rmtree(file_extract_path)
                return Response({
                    'error': 'La table attributaire de votre fichier ne contient pas les champs requis!!!',
                    'Champs requis': default_attributtes
                })

        else:
            return Response({'error': 'No Shapefile provided.'}, status=400)


class MunicipalityList(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        if 'id' not in kwargs:
            queryset = Municipality.objects.all()
            serializer = MunicipalitySerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            department = Municipality.objects.filter(pk=kwargs['id']).first()
            serializer = MunicipalitySerializer(department)
            return Response(serializer.data, status=status.HTTP_200_OK)


class MunicipalityListForMobile(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        queryset = Municipality.objects.all()
        serializer = MunicipalityDropdownSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MunicipalityDropdownList(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        if 'department_id' not in kwargs:
            queryset = Municipality.objects.all()
            serializer = MunicipalityDropdownSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = Municipality.objects.filter(department_id=kwargs['department_id']).all()
            serializer = MunicipalityDropdownSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


class QuarterCreateView(APIView):
    queryset = Quarter.objects.all()
    serializer_class = QuarterCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        shapefile = request.FILES.get('file_field')
        default_attributtes = ['COMMUNES', 'NOM']
        if shapefile:
            # Save the uploaded file to the UploadedFile model
            new_file = FileUpload.objects.create(file=shapefile)
            file = new_file.file.path
            file_path = os.path.dirname(file)
            file_name = os.path.basename(file).split('.')[0]
            file_extract_path = os.path.join(file_path, file_name)
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(file_extract_path)

            os.remove(file)
            # we get the shapefile from the extracted zip file
            shp = glob.glob(r'{}/**/*.shp'.format(file_extract_path), recursive=True)[0]

            gdf = gpd.read_file(shp)
            my_crs = gdf.crs.to_epsg()
            # print(my_crs)
            if my_crs != out_epsg:
                gdf_new = gdf.to_crs(epsg=out_epsg)
                gdf_new.to_file(os.path.abspath(os.path.join(BASE_DIR, 'media/changed_data/changed_data.shp')))
                shp = os.path.abspath(os.path.join(BASE_DIR, 'media/changed_data/changed_data.shp'))

            # using ogr to interact with the shapefile
            try:
                datasource = ogr.Open(shp)
                layer = datasource.GetLayer(0)
                shapefile_ok = True
                print('Shapefile ok')
            except Exception as e:
                traceback.print_exc()
                shapefile_ok = False
                print(f"An error occurred: {str(e)}")
                print('Bad Shapefile')

            '''
            creating array to store attribute labels of the features
            '''
            attributes = []
            layer_def = layer.GetLayerDefn()
            for i in range(layer_def.GetFieldCount()):
                field_def = layer_def.GetFieldDefn(i)
                name = field_def.GetName()
                attributes.append(name)

            print(attributes)

            contains_value = any(item in default_attributtes for item in attributes)

            if contains_value is True:
                for i in range(layer.GetFeatureCount()):
                    src_feature = layer.GetFeature(i)
                    src_geometry = src_feature.GetGeometryRef()

                    '''
                    check if there is a feature missing geometry
                    '''
                    if src_geometry is not None:
                        '''
                        Check if the source and destination spatial ref are equal before transformation
                        helps prevent coordinate reversing
                        '''
                        # if str(src_spatial_ref) != str(dst_spatial_ref):
                        #     src_geometry.Transform(coord_transform)
                        #     print('hello i am not equal')

                        geometry = GEOSGeometry(src_geometry.ExportToWkt())

                        if geometry.geom_type != 'MultiPolygon':
                            geometry = MultiPolygon(geometry)
                        filtered_municipality = Municipality.objects.filter(
                            municipality_name__contains=src_feature.GetFieldAsString('COMMUNES'))
                        # print(filtered_department)
                        if len(filtered_municipality) != 0:
                            print(filtered_municipality[0])
                            quarter = Quarter(
                                quarter_name=src_feature.GetFieldAsString('NOM'),
                                municipality=filtered_municipality[0],
                                file=new_file,
                                geo=geometry
                            )
                            quarter.save()

                shutil.rmtree(file_extract_path)

                return Response({'message': 'Shapefile data uploaded successfully.'})
            else:
                shutil.rmtree(file_extract_path)
                return Response({
                    'error': 'La table attributaire de votre fichier ne contient pas les champs requis!!!',
                    'Champs requis': default_attributtes
                })

        else:
            return Response({'error': 'No Shapefile provided.'}, status=400)


class QuarterList(APIView):
    pagination_class = CustomPageNumberPagination  # Apply your custom pagination class
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        if 'id' not in kwargs:
            queryset = Quarter.objects.all()
            serializer = QuarterSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            queryset = Quarter.objects.filter(pk=kwargs['id']).first()
            serializer = QuarterSerializer(queryset)
            return Response(serializer.data, status=status.HTTP_200_OK)


class QuarterListView(ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = Quarter.objects.all()
    serializer_class = QuarterSerializer
    pagination_class = PageNumberPagination


class TypeRiskCreateView(APIView):
    queryset = TypeRisk.objects.all()
    serializer_class = TypeRiskSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        risk_type_label = request.POST.get('risk_type_label')
        TypeRisk.objects.create(risk_type_label=risk_type_label)
        return Response({'message': 'Risk type created successfully.'}, status=200)


class TypeRiskList(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        queryset = TypeRisk.objects.all()
        serializer = TypeRiskSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RiskCreateView(APIView):
    queryset = Risk.objects.all()
    serializer_class = RiskCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        shapefile = request.FILES.get('file_field')
        risk_label = request.POST.get('risk_label')
        type_risk = TypeRisk.objects.filter(
            pk=request.POST.get('type_risk'))
        default_attributtes = ['COMMUNE', 'NOM']
        if shapefile:
            # Save the uploaded file to the UploadedFile model
            new_file = FileUpload.objects.create(file=shapefile)
            file = new_file.file.path
            file_path = os.path.dirname(file)
            file_name = os.path.basename(file).split('.')[0]
            file_extract_path = os.path.join(file_path, file_name)
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(file_extract_path)

            os.remove(file)
            # we get the shapefile from the extracted zip file
            shp = glob.glob(r'{}/**/*.shp'.format(file_extract_path), recursive=True)[0]

            gdf = gpd.read_file(shp)
            my_crs = None
            print(gdf.crs)
            if gdf.crs is not None:
                my_crs = gdf.crs.to_epsg()
            # print(my_crs)
            if my_crs != out_epsg:
                gdf_new = gdf.to_crs(epsg=out_epsg)
                gdf_new.to_file(os.path.abspath(os.path.join(BASE_DIR, f'media/{file_name}/changed_data.shp')))
                shp = os.path.abspath(os.path.join(BASE_DIR, f'media/{file_name}/changed_data.shp'))

            # using ogr to interact with the shapefile
            try:
                datasource = ogr.Open(shp)
                layer = datasource.GetLayer(0)
                shapefile_ok = True
                print('Shapefile ok')
            except Exception as e:
                traceback.print_exc()
                shapefile_ok = False
                print(f"An error occurred: {str(e)}")
                print('Bad Shapefile')

            '''
            creating array to store attribute labels of the features
            '''
            attributes = []
            layer_def = layer.GetLayerDefn()
            for i in range(layer_def.GetFieldCount()):
                field_def = layer_def.GetFieldDefn(i)
                name = field_def.GetName()
                attributes.append(name)

            print(attributes)

            contains_value = any(item in default_attributtes for item in attributes)

            if contains_value is True:
                for i in range(layer.GetFeatureCount()):
                    src_feature = layer.GetFeature(i)
                    src_geometry = src_feature.GetGeometryRef()

                    '''
                    check if there is a feature missing geometry
                    '''
                    if src_geometry is not None:
                        '''
                        Check if the source and destination spatial ref are equal before transformation
                        helps prevent coordinate reversing
                        '''
                        # if str(src_spatial_ref) != str(dst_spatial_ref):
                        #     src_geometry.Transform(coord_transform)
                        #     print('hello i am not equal')

                        geometry = GEOSGeometry(src_geometry.ExportToWkt())

                        if geometry.geom_type != 'MultiPolygon':
                            geometry = MultiPolygon(geometry)

                        print(geometry.area * 10000)
                        risk_area = geometry.area * 10000
                        filtered_municipality = Municipality.objects.filter(
                            municipality_name__icontains=src_feature.GetFieldAsString('COMMUNE'))

                        print(src_feature.GetFieldAsString('COMMUNE'))
                        # if len(filtered_municipality) != 0:
                        print(filtered_municipality[0])
                        risk = Risk(
                            risk_label=risk_label,
                            municipality=filtered_municipality[0],
                            type_risk=type_risk[0],
                            area_affected=risk_area,
                            file=new_file,
                            geo=geometry
                        )
                        risk.save()

                shutil.rmtree(file_extract_path)

                return Response({'message': 'Shapefile data uploaded successfully.'})
            else:
                shutil.rmtree(file_extract_path)
                return Response({
                    'error': 'La table attributaire de votre fichier ne contient pas les champs requis!!!',
                    'Champs requis': default_attributtes
                })

        else:
            return Response({'error': 'No Shapefile provided.'}, status=400)


class RiskList(generics.ListAPIView):
    queryset = Risk.objects.all()
    serializer_class = RiskSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = super().get_queryset()
        element_id = self.request.query_params.get('id')
        print(element_id)
        if element_id:
            queryset = queryset.filter(id=element_id)
        return queryset


class RiskById(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        queryset = Risk.objects.filter(pk=kwargs['id']).first()
        serializer = RiskSerializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BuildingCreateView(APIView):
    queryset = Building.objects.all()
    serializer_class = BuildingCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        shapefile = request.FILES.get('file_field')
        building_state = request.POST.get('building_state')
        building_label = request.POST.get('building_label')
        default_attributtes = ['COMMUNE', 'QUARTIERS', 'INONDABLE', 'EXPLOSION']
        if shapefile:
            # Save the uploaded file to the UploadedFile model
            new_file = FileUpload.objects.create(file=shapefile)
            file = new_file.file.path
            file_path = os.path.dirname(file)
            file_name = os.path.basename(file).split('.')[0]
            file_extract_path = os.path.join(file_path, file_name)
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(file_extract_path)

            os.remove(file)
            # we get the shapefile from the extracted zip file
            shp = glob.glob(r'{}/**/*.shp'.format(file_extract_path), recursive=True)[0]

            gdf = gpd.read_file(shp)
            my_crs = None
            print(gdf.crs)
            if gdf.crs is not None:
                my_crs = gdf.crs.to_epsg()
            # print(my_crs)
            if my_crs != out_epsg:
                current_date_str = datetime.today()
                path = f'media/{current_date_str.year}/{current_date_str.month:02d}/{current_date_str.day}/{file_name}/4326'
                if not os.path.exists(os.path.join(BASE_DIR, path)):
                    # Create the directory
                    os.makedirs(os.path.join(BASE_DIR, path))
                gdf_new = gdf.to_crs(epsg=out_epsg)
                gdf_new.to_file(os.path.abspath(os.path.join(BASE_DIR, f'{path}/changed_data.shp')))
                shp = os.path.abspath(os.path.join(BASE_DIR, f'{path}/changed_data.shp'))

            # using ogr to interact with the shapefile
            try:
                datasource = ogr.Open(shp)
                layer = datasource.GetLayer(0)
                shapefile_ok = True
                print('Shapefile ok')
            except Exception as e:
                traceback.print_exc()
                shapefile_ok = False
                print(f"An error occurred: {str(e)}")
                print('Bad Shapefile')

            '''
            creating array to store attribute labels of the features
            '''
            attributes = []
            layer_def = layer.GetLayerDefn()
            for i in range(layer_def.GetFieldCount()):
                field_def = layer_def.GetFieldDefn(i)
                name = field_def.GetName()
                attributes.append(name)

            print(attributes)

            contains_value = any(item in default_attributtes for item in attributes)

            if contains_value is True:
                for i in range(layer.GetFeatureCount()):
                    src_feature = layer.GetFeature(i)
                    src_geometry = src_feature.GetGeometryRef()

                    '''
                    check if there is a feature missing geometry
                    '''
                    if src_geometry is not None:
                        '''
                        Check if the source and destination spatial ref are equal before transformation
                        helps prevent coordinate reversing
                        '''
                        # if str(src_spatial_ref) != str(dst_spatial_ref):
                        #     src_geometry.Transform(coord_transform)
                        #     print('hello i am not equal')

                        geometry = GEOSGeometry(src_geometry.ExportToWkt())

                        if geometry.geom_type != 'MultiPolygon':
                            geometry = MultiPolygon(geometry)

                        # print(geometry.area * 10000)
                        building_area = geometry.area * 10000
                        filtered_municipality = Municipality.objects.filter(
                            municipality_name__icontains=src_feature.GetFieldAsString('COMMUNE'))
                        filtered_quarter = Quarter.objects.filter(
                            quarter_name__icontains=src_feature.GetFieldAsString('QUARTIERS'))
                        #
                        # print(f"{src_feature.GetFieldAsString('QUARTIERS')} -> {src_feature.GetFieldAsString('COMMUNE')}")
                        if len(filtered_quarter) != 0:
                            building = Building(
                                building_label=building_label,
                                municipality=filtered_quarter[0].municipality,
                                quarter=filtered_quarter[0],
                                building_state=1,
                                building_area=building_area,
                                file=new_file,
                                geo=geometry
                            )
                        elif len(filtered_municipality) != 0:
                            building = Building(
                                building_label=building_label,
                                municipality=filtered_municipality[0],
                                building_state=1,
                                building_area=building_area,
                                file=new_file,
                                geo=geometry
                            )
                        else:
                            building = Building(
                                building_label=building_label,
                                building_state=1,
                                building_area=building_area,
                                file=new_file,
                                geo=geometry
                            )
                        building.save()

                # shutil.rmtree(file_extract_path)

                return Response({'message': 'Shapefile data uploaded successfully.'})
            else:
                # shutil.rmtree(file_extract_path)
                return Response({
                    'error': 'La table attributaire de votre fichier ne contient pas les champs requis!!!',
                    'Champs requis': default_attributtes
                })

        else:
            return Response({'error': 'No Shapefile provided.'}, status=400)


class BuildingById(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        queryset = Building.objects.filter(pk=kwargs['id']).first()
        serializer = BuildingSerializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BuildingList(generics.ListAPIView):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


class StationCreateView(APIView):
    queryset = GasStation.objects.all()
    serializer_class = StationCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        shapefile = request.FILES.get('file_field')
        default_attributtes = ['COMMUNE', 'QUARTIER', 'NOM', 'TYPE']
        if shapefile:
            # Save the uploaded file to the UploadedFile model
            new_file = FileUpload.objects.create(file=shapefile)
            file = new_file.file.path
            file_path = os.path.dirname(file)
            file_name = os.path.basename(file).split('.')[0]
            file_extract_path = os.path.join(file_path, file_name)
            with zipfile.ZipFile(file, 'r') as zip_ref:
                zip_ref.extractall(file_extract_path)

            os.remove(file)
            # we get the shapefile from the extracted zip file
            shp = glob.glob(r'{}/**/*.shp'.format(file_extract_path), recursive=True)[0]

            gdf = gpd.read_file(shp)
            my_crs = None
            print(gdf.crs)
            if gdf.crs is not None:
                my_crs = gdf.crs.to_epsg()
            # print(my_crs)
            if my_crs != out_epsg:
                gdf_new = gdf.to_crs(epsg=out_epsg)
                gdf_new.to_file(os.path.abspath(os.path.join(BASE_DIR, f'media/{file_name}/changed_data.shp')))
                shp = os.path.abspath(os.path.join(BASE_DIR, f'media/{file_name}/changed_data.shp'))

            # using ogr to interact with the shapefile
            try:
                datasource = ogr.Open(shp)
                layer = datasource.GetLayer(0)
                shapefile_ok = True
                print('Shapefile ok')
            except Exception as e:
                traceback.print_exc()
                shapefile_ok = False
                print(f"An error occurred: {str(e)}")
                print('Bad Shapefile')

            '''
            creating array to store attribute labels of the features
            '''
            attributes = []
            layer_def = layer.GetLayerDefn()
            for i in range(layer_def.GetFieldCount()):
                field_def = layer_def.GetFieldDefn(i)
                name = field_def.GetName()
                attributes.append(name)

            print(attributes)

            contains_value = any(item in default_attributtes for item in attributes)

            if contains_value is True:
                for i in range(layer.GetFeatureCount()):
                    src_feature = layer.GetFeature(i)
                    src_geometry = src_feature.GetGeometryRef()

                    '''
                    check if there is a feature missing geometry
                    '''
                    if src_geometry is not None:
                        '''
                        Check if the source and destination spatial ref are equal before transformation
                        helps prevent coordinate reversing
                        '''
                        # if str(src_spatial_ref) != str(dst_spatial_ref):
                        #     src_geometry.Transform(coord_transform)
                        #     print('hello i am not equal')

                        geometry = GEOSGeometry(src_geometry.ExportToWkt())

                        if geometry.geom_type != 'MultiPoint':
                            geometry = MultiPoint(geometry)

                        filtered_municipality = Municipality.objects.filter(
                            municipality_name__icontains=src_feature.GetFieldAsString('COMMUNE'))

                        filtered_quarter = Quarter.objects.filter(
                            quarter_name__icontains=src_feature.GetFieldAsString('QUARTIER'))
                        # if len(filtered_municipality) != 0:
                        print(src_feature.GetFieldAsString('QUARTIER'))
                        if filtered_quarter:
                            gas_station = GasStation(
                                name_station=src_feature.GetFieldAsString('TYPE'),
                                municipality=filtered_municipality[0],
                                quarter=filtered_quarter[0],
                                geo=geometry
                            )
                        else:
                            gas_station = GasStation(
                                name_station=src_feature.GetFieldAsString('TYPE'),
                                municipality=filtered_municipality[0],
                                # quarter=filtered_quarter[0],
                                geo=geometry
                            )
                        gas_station.save()

                shutil.rmtree(file_extract_path)

                return Response({'message': 'Shapefile data uploaded successfully.'})
            else:
                shutil.rmtree(file_extract_path)
                return Response({
                    'error': 'La table attributaire de votre fichier ne contient pas les champs requis!!!',
                    'Champs requis': default_attributtes
                })

        else:
            return Response({'error': 'No Shapefile provided.'}, status=400)


class GasStationList(generics.ListAPIView):
    queryset = GasStation.objects.all()
    serializer_class = StationSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


class GasStationById(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        queryset = GasStation.objects.filter(pk=kwargs['id']).first()
        serializer = StationSerializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoadCreateView(APIView):
    queryset = Road.objects.all()
    serializer_class = RoadCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, format=None):
        shapefile = request.FILES.get('file_field')
        default_attributtes = ['TYPE_ROUTE']
        extensions_to_check = ['.cpg', '.dbf', '.prj', '.shp', '.shx']
        if shapefile:
            # Save the uploaded file to the UploadedFile model
            new_file = FileUpload.objects.create(file=shapefile)
            file = new_file.file.path
            file_path = os.path.dirname(file)
            file_name = os.path.basename(file).split('.')[0]
            file_extract_path = os.path.join(file_path, file_name)
            zipFileStatus = check_zip_for_extensions(file, extensions_to_check)

            if zipFileStatus:
                with zipfile.ZipFile(file, 'r') as zip_ref:
                    zip_ref.extractall(file_extract_path)

                os.remove(file)
                # we get the shapefile from the extracted zip file
                shp = glob.glob(r'{}/**/*.shp'.format(file_extract_path), recursive=True)[0]

                gdf = gpd.read_file(shp)
                my_crs = None
                print(gdf.crs)
                if gdf.crs is not None:
                    my_crs = gdf.crs.to_epsg()
                # print(my_crs)
                if my_crs != out_epsg:
                    current_date_str = datetime.today()
                    path = f'media/{current_date_str.year}/{current_date_str.month:02d}/{current_date_str.day}/{file_name}/4326'
                    if not os.path.exists(os.path.join(BASE_DIR, path)):
                        # Create the directory
                        os.makedirs(os.path.join(BASE_DIR, path))
                    gdf_new = gdf.to_crs(epsg=out_epsg)
                    gdf_new.to_file(os.path.abspath(os.path.join(BASE_DIR, f'{path}/changed_data.shp')))
                    shp = os.path.abspath(os.path.join(BASE_DIR, f'{path}/changed_data.shp'))

                # using ogr to interact with the shapefile
                try:
                    datasource = ogr.Open(shp)
                    layer = datasource.GetLayer(0)
                    shapefile_ok = True
                    print('Shapefile ok')
                except Exception as e:
                    traceback.print_exc()
                    shapefile_ok = False
                    print(f"An error occurred: {str(e)}")
                    print('Bad Shapefile')

                '''
                creating array to store attribute labels of the features
                '''
                attributes = []
                layer_def = layer.GetLayerDefn()
                for i in range(layer_def.GetFieldCount()):
                    field_def = layer_def.GetFieldDefn(i)
                    name = field_def.GetName()
                    attributes.append(name)

                print(attributes)

                contains_value = any(item in default_attributtes for item in attributes)

                if contains_value is True:
                    for i in range(layer.GetFeatureCount()):
                        src_feature = layer.GetFeature(i)
                        src_geometry = src_feature.GetGeometryRef()

                        '''
                        check if there is a feature missing geometry
                        '''
                        if src_geometry is not None:
                            '''
                            Check if the source and destination spatial ref are equal before transformation
                            helps prevent coordinate reversing
                            '''
                            # if str(src_spatial_ref) != str(dst_spatial_ref):
                            #     src_geometry.Transform(coord_transform)
                            #     print('hello i am not equal')

                            geometry = GEOSGeometry(src_geometry.ExportToWkt())
                            # print(geometry.geom_type)

                            if geometry.geom_type != 'MultiLineString':
                                geometry = MultiLineString(geometry)

                            road_distance = geometry.length
                            road = Road(
                                road_name=src_feature.GetFieldAsString('TYPE_ROUTE'),
                                road_distance=road_distance,
                                # quarter=filtered_quarter[0],
                                geo=geometry
                            )
                            road.save()

                    shutil.rmtree(file_extract_path)

                    return Response({'message': 'Shapefile data uploaded successfully.'}, status=status.HTTP_200_OK)
                else:
                    shutil.rmtree(file_extract_path)
                    return Response({
                        'error': 'La table attributaire de votre fichier ne contient pas les champs requis!!!',
                        'Champs_requis': default_attributtes
                    }, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

            else:
                return Response({
                    'error': 'Dossier .zip ne contenant pas le fichier .shp .',
                    'Champs_requis': extensions_to_check
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No Shapefile provided.'}, status=status.HTTP_400_BAD_REQUEST)


class RoadList(generics.ListAPIView):
    queryset = Road.objects.all()
    serializer_class = RoadSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


class RoadById(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        queryset = Road.objects.filter(pk=kwargs['id']).first()
        serializer = RoadSerializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RiskAreaList(generics.ListAPIView):
    queryset = RiskArea.objects.all()
    serializer_class = RiskAreaSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


class RiskAreaById(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        queryset = RiskArea.objects.filter(pk=kwargs['id']).first()
        serializer = RiskAreaSerializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RiskAreaCreateView(APIView):
    queryset = RiskArea.objects.all()
    serializer_class = RiskAreaCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, **kwargs):
        try:
            geo = Point(x=float(request.POST['longitude']), y=float(request.POST['latitude']), srid=out_epsg)
            area_name = request.POST['area_name']
            municipality = request.POST['municipality']
            type_risk = request.POST['type_risk']
            if request.FILES:
                risk_area = RiskArea(area_name=area_name, municipality_id=municipality, type_risk_id=type_risk,
                                     geo=MultiPoint(geo), file=request.FILES['file'], image_uploaded=True)
            else:
                risk_area = RiskArea(area_name=area_name, municipality_id=municipality, type_risk_id=type_risk,
                                     geo=MultiPoint(geo), file='pictures/icon-missing-picture.jpeg')
            risk_area.save()
            return Response(status=status.HTTP_200_OK)
        except HTTPError as e:
            status_code = e.response.status_code
            return Response(status=status_code)


class RiskAreaUpdateView(generics.UpdateAPIView):
    queryset = RiskArea.objects.all()
    serializer_class = RiskAreaCreateSerializer
    permission_classes = (permissions.AllowAny,)

    def put(self, request, *args, **kwargs):
        # print(request.data)
        try:
            geo = Point(x=float(request.data['longitude']), y=float(request.data['latitude']), srid=out_epsg)
            area_name = request.data['area_name']
            municipality = request.data['municipality']
            type_risk = request.data['type_risk']
            risk_area = RiskArea.objects.get(pk=kwargs['id'])
            risk_area.area_name = area_name
            risk_area.municipality_id = municipality
            risk_area.type_risk_id = type_risk
            risk_area.geo = MultiPoint(geo)
            if request.FILES:
                risk_area.file = request.FILES['file']
                risk_area.image_uploaded = True
            risk_area.save()
            return Response(status=status.HTTP_200_OK)
        except HTTPError() as e:
            print(e.e.response.raise_for_status)
            status_code = e.response.status_code
            status_message = e.response.raise_for_status
            return Response({'msg': status_message}, status=status_code)
