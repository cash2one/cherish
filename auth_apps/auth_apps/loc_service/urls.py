from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    GetProvinceAPIView, GetCityAPIView, GetAreaAPIView,
    GetLocationFuzzleAPIView
)


api_urlpatterns = [
    url(
        r'^loc/pro/$',
        GetProvinceAPIView.as_view(),
        name='api_get_province'
    ),
    url(
        r'^loc/city/(?P<pk>\d+)/$',
        GetCityAPIView.as_view(),
        name='api_get_city'
    ),
    url(
        r'^loc/area/(?P<pk>\d+)/$',
        GetAreaAPIView.as_view(),
        name='api_get_area'
    ),
    url(
        r'^loc/fuzzle/$',
        GetLocationFuzzleAPIView.as_view(),
        name='api_get_fuzzle_location'
    )
]

versioned_api_urlpatterns = [
    url(r'^api/v1/', include(api_urlpatterns, namespace='v1')),
]
urlpatterns = format_suffix_patterns(versioned_api_urlpatterns, allowed=['json'])
