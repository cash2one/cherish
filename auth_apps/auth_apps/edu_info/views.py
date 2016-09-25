# -*- coding: utf-8 -*-

import base64
import logging
import urlparse

from django.db import transaction
from rest_framework import generics
from rest_framework.response import Response
from pyDes import des, ECB, PAD_PKCS5

from auth_user.exceptions import ParameterError
from loc_service.models import Location
from loc_service.conf import ANDTEACH
from .models import School
from .serializers import SchoolSerializer, SchoolIDNameSerializer

logger = logging.getLogger(__name__)


class GetSchoolAPIView(generics.GenericAPIView):
    def get(self, request, pk, *args, **kwargs):
        category = request.query_params.get('category')
        filters = {'area_code_id': pk}

        if category and category != -1:
            filters.update({'category': category})

        queryset = School.objects.filter(**filters)
        serializer = SchoolSerializer(queryset, many=True)

        response = {
            'data': serializer.data,
            'code': 1,
            'msg': 'success'
        }

        return Response(response)


class AddSchoolAPIView(generics.GenericAPIView):

    CHR_KEY = [49, 55, 100, 98, 44, 56, 52, 52]
    PASSWD = ''.join(map(chr, CHR_KEY))

    def encrypt(cls, data, passwd):
        data = data.encode('utf-8')
        k = des(passwd, ECB, pad=None, padmode=PAD_PKCS5)
        return base64.b64encode(k.encrypt(data))

    def decrypt(cls, data, passwd):
        k = des(passwd, ECB, pad=None, padmode=PAD_PKCS5)
        return k.decrypt(base64.b64decode(data))

    def get(self, request, *args, **kwargs):
        area_code = request.query_params.get('district')
        school_name = request.query_params.get('name')
        data = request.query_params.get('key')

        decrypt_body = self.decrypt(data, self.PASSWD)
        try:
            d = dict([(k, v[0])
                     for k, v in urlparse.parse_qs(decrypt_body).items()])
            if d['district'] == area_code and d['name'] == school_name:
                area = Location.objects.get(pk=area_code)
                School.objects.create(name=school_name,
                                      area_code_id=area.pk,
                                      source=School.SCHOOL_SOURCE.USER)
        except:
            response = {'code': 0, 'msg': 'fail'}
        else:
            response = {'code': 1, 'msg': 'success'}
        return Response(response)


class GetSchoolIDAPIView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        area_code = request.query_params.get('district')
        school_name = request.query_params.get('name')
        category = request.query_params.get('category')

        filters = {
            'area_code_id': area_code,
            'name': school_name
        }

        if category is not None and category != -1:
            filters.update({'category': category})

        try:
            school = School.objects.get(**filters)
            response = {
                'id': school.pk,
                'code': 1,
                'msg': 'success'
            }
        except School.DoesNotExist:
            response = {
                'code': 0,
                'msg': 'fail'
            }
        return Response(response)


class GetFuzzleSchoolAPIView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        school_name = request.query_params.get('name')
        area_code = request.query_params.get('district')
        category = request.query_params.get('category')

        filters = {'name__contains': school_name}

        if category is not None and category != -1:
            filters.update({'category': category})

        if area_code is not None and area_code != -1:
            filters.update({'area_code_id': area_code})

        queryset = School.objects.filter(**filters)
        serializer = SchoolSerializer(queryset, many=True)
        schools = serializer.data

        response = {
            'schools': schools,
            'code': 1,
            'count': len(schools),
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
            raise ParameterError("province or city or area or school empty")

        try:
            category = int(category)
        except:
            raise ParameterError("category invalid")
        # province
        try:
            # do exact query first
            province = Location.objects.get(name=province_name, parent=None)
        except Location.DoesNotExist:
            try:
                province = Location.objects.get(name__contains=province_name, parent=None)
            except (Location.DoesNotExist, Location.MultipleObjectsReturned):
                raise ParameterError("province invalid")
        except Location.MultipleObjectsReturned:
            raise ParameterError("province invalid, multiple found")
        # city
        try:
            city = province.children.get(name=city_name)
        except Location.DoesNotExist:
            try:
                city = province.children.get(name__contains=city_name)
            except (Location.DoesNotExist, Location.MultipleObjectsReturned):
                raise ParameterError("city invalid")
        except Location.MultipleObjectsReturned:
            raise ParameterError("city invalid, multiple found")
        # area
        area_name = ANDTEACH.get(area_name, area_name)
        if area_name:
            try:
                area = city.children.get(name=area_name)
            except Location.DoesNotExist:
                try:
                    area = city.children.get(name__contains=area_name)
                except (Location.DoesNotExist, Location.MultipleObjectsReturned):
                    raise ParameterError("area invalid")
            except Location.MultipleObjectsReturned:
                raise ParameterError("area invalid, multiple found")
        else:
            area = city

        with transaction.atomic():
            school, created = area.schools.get_or_create(
                name=school_name, category=category,
                defaults={
                    'area_code': area,
                    'source': School.SCHOOL_SOURCE.USER
                })
            if created:
                # create new school
                logger.warn('create new school: {s}'.format(s=school))

        response = {
            'province_code': province.code,
            'city_code': city.code,
            'area_code': area.code,
            'school_id': school.school_id
        }
        return Response(response)
