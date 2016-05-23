import logging

from rest_framework import serializers

from .models import School

logger = logging.getLogger(__name__)


class SchoolSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField('custom_get_school_id')
    areaCode = serializers.SerializerMethodField('custom_get_area_code_id')

    def custom_get_school_id(self, instance):
        return instance.school_id

    def custom_get_area_code_id(self, instance):
        return instance.area_code_id

    class Meta:
        model = School
        fields = (
            'name', 'pinyin', 'category', 'id', 'areaCode'
        )
