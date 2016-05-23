import logging

from rest_framework import serializers

from edu_info.models import School
from .models import Location

logger = logging.getLogger(__name__)


class ProvinceSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField('custom_get_tree_lft')

    def custom_get_tree_lft(self, instance):
        return instance.lft

    class Meta:
        model = Location
        fields = (
            'code', 'name', 'id'
        )


class AreaSerializer(ProvinceSerializer):
    fatherCode = serializers.SerializerMethodField('custom_get_father_code')

    def custom_get_father_code(self, instance):
        return instance.parent_id

    class Meta(ProvinceSerializer.Meta):
        fields = ProvinceSerializer.Meta.fields + ('fatherCode', )


class CitySerializer(AreaSerializer):
    count = serializers.SerializerMethodField('custom_get_count')

    def custom_get_count(self, instance):
        area_code_ids = [
            obj.code for obj in Location.objects.filter(parent_id=instance.code)]
        return School.objects.filter(area_code_id__in=area_code_ids).count()

    class Meta(AreaSerializer.Meta):
        fields = AreaSerializer.Meta.fields + ('count', )
