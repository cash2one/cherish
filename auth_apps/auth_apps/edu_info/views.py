import logging

from rest_framework import generics
from rest_framework.response import Response

from auth_user.exceptions import ParameterError
from loc_service.models import Location
from .models import School
from .serializers import SchoolSerializer, SchoolIDNameSerializer

logger = logging.getLogger(__name__)


class GetSchoolAPIView(generics.GenericAPIView):
    def get(self, request, pk, *args, **kwargs):
        queryset = School.objects.filter(**{
            'area_code_id': pk
        })
        serializer = SchoolSerializer(queryset, many=True)
        response = {
            'data': serializer.data,
            'code': 1,
            'msg': 'success'
        }
        return Response(response)


class GetSchoolIDNameAPIView(generics.GenericAPIView):
    def get(self, request, pk, *args, **kwargs):
        queryset = School.objects.filter(**{
            'area_code_id': pk
        })
        serializer = SchoolIDNameSerializer(queryset, many=True)
        response = {
            'data': serializer.data,
            'code': 1,
            'msg': 'success'
        }
        return Response(response)


class GetOrCreateSchoolAPIView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        province_name = request.data.get('province')
        city_name = request.data.get('city')
        area_name = request.data.get('area')
        school_name = request.data.get('school')
        category = request.data.get('category')

        if not (province_name and city_name and area_name and school_name):
            raise ParameterError("province or city or area or school invalid ")

        try:
            category = int(category)
        except:
            raise ParameterError("category invalid")

        try:
            province = Location.objects.get(name__contains=province_name)
            city = province.children.get(name__contains=city_name)
            area = city.children.get(name__contains=area_name)
        except (Location.DoesNotExist, Location.MultipleObjectsReturned):
            raise ParameterError("province or city or area invalid")

        try:
            school = area.schools.get(name__contains=school_name)
            if school.category != category:
                school.category = category
                school.save()
        except School.DoesNotExist:
            school = School.objects.create(
                name=school_name,
                area_code=area,
                category=category
            )
        except School.MultipleObjectsReturned:
            raise ParameterError("school invalid")

        response = {
            'province_code': province.code,
            'city_code': city.code,
            'area_code': area.code,
            'school_id': school.school_id
        }
        return Response(response)
