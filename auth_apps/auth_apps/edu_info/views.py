import logging

from rest_framework import generics
from rest_framework.response import Response

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
