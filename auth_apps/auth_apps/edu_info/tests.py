# -*- coding: utf-8 -*-

import urllib
import logging

from django.core.cache import cache
from django.core.urlresolvers import reverse_lazy
from rest_framework.test import APITestCase
from rest_framework import status

from loc_service.models import Location
from .models import School


logger = logging.getLogger(__name__)


def build_url(*args, **kwargs):
    get = kwargs.pop('get', {})
    url = reverse_lazy(*args, **kwargs)
    if get:
        url += '?' + urllib.urlencode(get)
    return url


class GetSchoolTestCase(APITestCase):
    def setUp(self):
        cache.clear()

        self.location = Location.objects.create(code=110000, name='北京')
        self.primary = School.objects.create(name='experimental primary school',
                                             area_code_id=self.location.pk,
                                             category=1)
        self.middle = School.objects.create(name='experimental middle school',
                                            area_code_id=self.location.pk,
                                            category=2)

    def tearDown(self):
        cache.clear()

    def test_minimal_get(self):
        get_primary_url = build_url('education:v1:api_get_school',
                                    kwargs={'pk': self.location.pk},
                                    get={'category': 1})
        response = self.client.get(get_primary_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('data')), 1)

        get_all_url = build_url('education:v1:api_get_school',
                                kwargs={'pk': self.location.pk})
        response = self.client.get(get_all_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('data')), 2)


class AddSchoolTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        chr_key = [49, 55, 100, 98, 44, 56, 52, 52]
        self.passwd = ''.join(map(chr, chr_key))
        self.location = Location.objects.create(code=110000, name='北京')

    def tearDown(self):
        cache.clear()

    @staticmethod
    def encrypt(data, passwd):
        import base64
        from pyDes import des, ECB, PAD_PKCS5
        data = data.encode('utf-8')
        k = des(passwd, ECB, pad=None, padmode=PAD_PKCS5)
        return base64.b64encode(k.encrypt(data))

    def test_minimal_add(self):
        self.assertEqual(School.objects.count(), 0)

        district = self.location.pk
        name = 'experimental middle school'
        data = 'district={d}&name={n}'.format(d=district, n=name)
        key = self.encrypt(data, self.passwd)

        kwargs = {
            'district': district,
            'name': name,
            'key': key
        }
        add_url = build_url('education:v1:api_add_school', get=kwargs)

        response = self.client.get(add_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(School.objects.count(), 1)


class GetSchoolIDTestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.location = Location.objects.create(code=110000, name='北京')
        self.name = 'experimental primary school'
        self.category = 1
        self.school = School.objects.create(name=self.name,
                                            area_code_id=self.location.pk,
                                            category=self.category)

    def tearDown(self):
        self.school.delete()
        self.location.delete()
        cache.clear()

    def test_minimal_get(self):
        kwargs = {
            'district': self.location.pk,
            'name': self.name,
            'category': self.category
        }
        get_url = build_url('education:v1:api_get_school_id', get=kwargs)

        response = self.client.get(get_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('id'), self.school.pk)


class GetFuzzleSchoolTestCase(APITestCase):
    def setUp(self):
        cache.clear()

        self.location = Location.objects.create(code=110000, name='北京')
        self.primary = School.objects.create(name='experimental primary school',
                                             area_code_id=self.location.pk,
                                             category=1)
        self.middle = School.objects.create(name='experimental middle school',
                                            area_code_id=self.location.pk,
                                            category=2)

    def tearDown(self):
        cache.clear()

    def test_minimal_get(self):
        kwargs = {
            'name': 'exper',
            'area_code': self.location.pk,
        }
        get_url = build_url('education:v1:api_get_fuzzle_school', get=kwargs)
        response = self.client.get(get_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('schools')), 2)


class GetOrCreateSchoolAPITestCase(APITestCase):
    def setUp(self):
        cache.clear()
        # province
        self.province = Location.objects.create(code=1, name='广东省')
        # city
        self.city = Location.objects.create(code=2, name='河源市', parent=self.province)
        # area
        self.area = Location.objects.create(code=3, name='龙川县', parent=self.city)

    def tearDown(self):
        cache.clear()

    def test_create_school_success(self):
        self.assertEqual(School.objects.count(), 0)
        url = reverse_lazy('education:v1:api_get_or_create_school')
        data = {
            'province': '广东',
            'city': '河源',
            'area': '龙川',
            'school': '老隆中学',
            'category': 2,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(School.objects.count(), 1)
        school = School.objects.get()
        self.assertTrue(school)
        correct_response = {
            'province_code': self.province.code,
            'city_code': self.city.code,
            'area_code': self.area.code,
            'school_id': school.school_id,
        }
        self.assertEqual(response.data, correct_response)

    def test_create_school_fail_due_to_invalid_area(self):
        self.assertEqual(School.objects.count(), 0)
        url = reverse_lazy('education:v1:api_get_or_create_school')
        data = {
            'province': '广东',
            'city': '河源',
            'area': 'invalid_area',
            'school': '老隆中学',
            'category': 2,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'area invalid'})
        self.assertEqual(School.objects.count(), 0)

    def test_create_school_fail_due_to_invalid_city(self):
        self.assertEqual(School.objects.count(), 0)
        url = reverse_lazy('education:v1:api_get_or_create_school')
        data = {
            'province': '广东',
            'city': 'invalid_city',
            'area': '龙川',
            'school': '老隆中学',
            'category': 2,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'city invalid'})
        self.assertEqual(School.objects.count(), 0)

    def test_create_school_fail_due_to_duplicated_city(self):
        dup_city = Location.objects.create(code=4, name='河源', parent=self.province)
        self.assertEqual(School.objects.count(), 0)
        url = reverse_lazy('education:v1:api_get_or_create_school')
        data = {
            'province': '广东',
            'city': '河',
            'area': '龙川',
            'school': '老隆中学',
            'category': 2,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'city invalid'})
        self.assertEqual(School.objects.count(), 0)

    def test_use_exist_school_success(self):
        exist_school = School.objects.create(
            name='老隆中学',
            area_code=self.area,
            category=2
        )
        self.assertEqual(School.objects.count(), 1)
        url = reverse_lazy('education:v1:api_get_or_create_school')
        data = {
            'province': '广东省',
            'city': '河源市',
            'area': '龙川',
            'school': '老隆中学',
            'category': 2,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(School.objects.count(), 1)
        correct_response = {
            'province_code': self.province.code,
            'city_code': self.city.code,
            'area_code': self.area.code,
            'school_id': exist_school.school_id,
        }
        self.assertEqual(response.data, correct_response)
