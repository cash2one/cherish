import logging

from django import template

from common.utils import enum
from loc_service.models import Location

logger = logging.getLogger(__name__)
register = template.Library()

LOC_LEVEL = enum(
    PROVINCE=0,
    CITY=1,
    AREA=2
)


@register.inclusion_tag('tags/province_tag.html')
def location_province():
    province = [{'pk': obj.pk, 'name': obj.name}
                for obj in Location.objects.filter(level=LOC_LEVEL.PROVINCE)]
    return {'province': province}


@register.inclusion_tag('tags/city_tag.html')
def location_city(pk):
    city = [{'pk': obj.pk, 'name': obj.name}
            for obj in Location.objects.filter(level=LOC_LEVEL.CITY,
                                               parent_id=pk)]
    return {'city': city}


@register.inclusion_tag('tags/area_tag.html')
def location_area(pk):
    area = [{'pk': obj.pk, 'name': obj.name}
            for obj in Location.objects.filter(level=LOC_LEVEL.AREA,
                                               parent_id=pk)]
    return {'area': area}
