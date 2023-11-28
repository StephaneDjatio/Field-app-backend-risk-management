from django.contrib import admin
from django.apps import apps

# Register your models here.
api_model = apps.get_app_config('api').get_models()

for model in api_model:
    admin.site.register(model)
