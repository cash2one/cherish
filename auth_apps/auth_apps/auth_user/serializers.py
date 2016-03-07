from django.contrib.auth.models import Group
from rest_framework import serializers

from .models import TechUUser


class TechUUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechUUser
        fields = (
            'user', 'email', 'birth_date', 'qq', 'remark', 
            'mobile', 'phone', 'address'
        )
        exclude = ('password', )


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
