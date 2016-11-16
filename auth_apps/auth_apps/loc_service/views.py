import logging

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from common.utils import enum
from .models import Location
from .serializers import (
    ProvinceSerializer, CitySerializer, AreaSerializer,
    LocationFuzzleSerializer
)

logger = logging.getLogger(__name__)

LOC_LEVEL = enum(
    PROVINCE=0,
    CITY=1,
    AREA=2,
)


class LocationUserRateThrottle(UserRateThrottle):
    rate = '100/minute'


class GetProvinceAPIView(generics.GenericAPIView):
    throttle_classes = (LocationUserRateThrottle,)

    def get(self, request, *args, **kwargs):
        queryset = Location.objects.filter(level=LOC_LEVEL.PROVINCE)
        serializer = ProvinceSerializer(queryset, many=True)
        response = {
            'data': serializer.data,
            'code': 1,
            'msg': 'success'
        }
        return Response(response)


class GetCityAPIView(generics.GenericAPIView):
    throttle_classes = (LocationUserRateThrottle,)

    def get(self, request, pk, *args, **kwargs):
        queryset = Location.objects.filter(**{
            'level': LOC_LEVEL.CITY,
            'parent_id': pk
        })
        serializer = CitySerializer(queryset, many=True)
        response = {
            'data': serializer.data,
            'code': 1,
            'msg': 'success'
        }
        return Response(response)


class GetAreaAPIView(generics.GenericAPIView):
    throttle_classes = (LocationUserRateThrottle,)

    def get(self, request, pk, *args, **kwargs):
        queryset = Location.objects.filter(**{
            'level': LOC_LEVEL.AREA,
            'parent_id': pk
        })
        serializer = AreaSerializer(queryset, many=True)
        response = {
            'data': serializer.data,
            'code': 1,
            'msg': 'success'
        }
        return Response(response)


class GetLocationFuzzleAPIView(generics.GenericAPIView):
    throttle_classes = (LocationUserRateThrottle,)

    def get(self, request, *args, **kwargs):
        keyword = request.query_params.get('keyword')
        queryset = Location.objects.filter(name__contains=keyword)
        serializer = LocationFuzzleSerializer(queryset, many=True)
        response = {
            'data': serializer.data,
            'code': 1,
            'msg': 'success'
        }
        return Response(response)
