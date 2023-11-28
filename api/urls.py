from django.urls import path, include
from .views import *

urlpatterns = [
    # ...
    path('auth/', include('rest_framework.urls')),
    path('user-role/', UserRoleView.as_view(), name='user-role'),
    path('user-role/update/<int:pk>', UserRoleUpdate.as_view(), name='userRoleUpdate'),
    path('user-role/<int:id>', UserRoleId.as_view(), name='userRoleById'),

    path('user/', AppUserView.as_view(), name='user'),
    path('user/checkEmail', checkUserEmail, name='userCheckEmail'),
    path('user/update/<int:pk>', UserUpdate.as_view(), name='userUpdate'),
    path('user/<int:id>', AppUserView.as_view(), name='userById'),
    path('login/', UserLogin.as_view(), name='login'),
    path('logout/', UserLogout.as_view(), name='logout'),

    path('provinces/', ProvinceList.as_view(), name='province'),
    path('provinces/dropdown', ProvinceDropdownList.as_view(), name='provinceDropdown'),
    path('provinces/<int:id>', ProvinceList.as_view(), name='provinceById'),
    path('provinces/add', ProvinceCreateView.as_view(), name='province-create'),

    path('departments/', DepartmentList.as_view(), name='department'),
    path('departments/mobile', DepartmentListForMobile.as_view(), name='departmentMobile'),
    path('departments/dropdown/<int:province_id>', DepartmentDropdownListByProvince.as_view(), name='departmentByProvince'),
    path('departments/<int:id>', DepartmentList.as_view(), name='departmentById'),
    path('departments/add', DepartmentCreateView.as_view(), name='department-create'),

    path('municipalities/', MunicipalityList.as_view(), name='municipality'),
    path('municipalities/mobile', MunicipalityListForMobile.as_view(), name='municipality'),
    path('municipalities_dropdown/', MunicipalityDropdownList.as_view(), name='municipalityDropdown'),
    path('municipalities_dropdown/<int:department_id>', MunicipalityDropdownList.as_view(), name='municipalityDropdownByDepartment'),
    path('municipalities/<int:id>', MunicipalityList.as_view(), name='municipalityById'),
    path('municipalities/add', MunicipalityCreateView.as_view(), name='municipality-create'),

    path('quarter/', QuarterListView.as_view(), name='quarter'),
    path('quarters/', QuarterList.as_view(), name='quarter'),
    path('quarters/<int:id>', QuarterList.as_view(), name='quarterById'),
    path('quarters/add', QuarterCreateView.as_view(), name='quarter-create'),

    path('type-risks/', TypeRiskList.as_view(), name='type-risk'),
    path('type-risks/add', TypeRiskCreateView.as_view(), name='type-risk-create'),
    path('risks/', RiskList.as_view(), name='risks'),
    path('risks/<int:id>', RiskById.as_view(), name='risksById'),
    path('risks/add', RiskCreateView.as_view(), name='risk-create'),


    path('buildings/', BuildingList.as_view(), name='buildings'),
    path('buildings/<int:id>', BuildingById.as_view(), name='buildingsById'),
    path('buildings/add', BuildingCreateView.as_view(), name='buildings-create'),

    path('gas_station/', GasStationList.as_view(), name='gas-station'),
    path('gas_station/<int:id>', GasStationById.as_view(), name='gasStationById'),
    path('gas_station/add', StationCreateView.as_view(), name='gas-station-create'),

    path('road/', RoadList.as_view(), name='road'),
    path('road/<int:id>', RoadById.as_view(), name='roadById'),
    path('road/add', RoadCreateView.as_view(), name='road-create'),

    path('field-data/', RiskAreaList.as_view(), name='fieldData'),
    path('field-data/<int:id>', RiskAreaById.as_view(), name='fieldDataById'),
    path('field-data/add', RiskAreaCreateView.as_view(), name='fieldData-create'),
    path('field-data/update/<int:id>', RiskAreaUpdateView.as_view(), name='fieldData-create'),
    # ...
]