from django.contrib.auth.models import User, Group
from rest_framework import serializers

from .models import AuthUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User


class AuthUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AuthUser
        fields = (
            'user', 'birth_date', 'qq', 'remark', 
            'mobile', 'phone', 'address'
        )


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
