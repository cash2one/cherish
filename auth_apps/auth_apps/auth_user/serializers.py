import logging
from django.contrib.auth.models import Group
from rest_framework import serializers

from .models import TechUUser

logger = logging.getLogger(__name__)


class TechUUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechUUser
        fields = (
            'username', 'email', 'gender', 'birth_date', 'qq', 'remark',
            'mobile', 'phone', 'address', 'avatar', 'nickname', 'context'
        )


class TechUMobileUserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechUUser
        fields = (
            'mobile', 'password', 'gender', 'birth_date', 'qq', 'remark',
            'phone', 'address', 'avatar', 'nickname', 'context'
        )

    # override
    def create(self, validated_data):
        # generate username
        username = TechUUser.autogen_username()
        validated_data['username'] = username
        logger.debug('[NEW USER] profile( {p} )'.format(p=validated_data))
        return TechUUser.objects.create(**validated_data)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group


class TechUBackendUserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechUUser
        fields = (
            'username', 'email', 'password', 'gender', 'birth_date', 'qq',
            'remark', 'mobile', 'phone', 'address', 'avatar', 'context'
        )
