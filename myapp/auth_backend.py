from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


def auth(email, password):
    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            return user
        else:
            return None
    except User.DoesNotExist:
        return None
