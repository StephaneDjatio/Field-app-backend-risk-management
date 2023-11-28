from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.http import QueryDict

UserModel = get_user_model()


def custom_validation(data):
    email = data['email'].strip()
    username = data['username'].strip()
    password = data['password'].strip()
    ##
    if not email or UserModel.objects.filter(email=email).exists():
        raise ValidationError('choose another email')
    ##
    if not password or len(password) < 8:
        raise ValidationError('choose another password, min 8 characters')
    ##
    if not username:
        raise ValidationError('choose another username')
    return data


def validate_email(data):
    email = data['email'].strip()
    if not email:
        raise ValidationError('an email is needed')
    return True


def validate_username(data):
    username = data['username'].strip()
    if not username:
        raise ValidationError('choose another username')
    return True


def validate_password(data):
    password = data['password'].strip()
    if not password:
        raise ValidationError('a password is needed')
    return True


def clean_data_validation(data):
    new_data = {}
    if isinstance(data, QueryDict):
        new_data = {key: value for key, value in data.items()}
    else:
        new_data = data
    for item in new_data:
        if not new_data[item].isdigit():
            new_data[item] = new_data[item].strip()

    return new_data
