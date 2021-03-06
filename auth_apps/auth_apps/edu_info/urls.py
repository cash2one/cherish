from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    GetSchoolAPIView, AddSchoolAPIView, GetSchoolIDAPIView,
    GetFuzzleSchoolAPIView, GetSchoolIDNameAPIView, GetOrCreateSchoolAPIView
)


api_urlpatterns = [
    url(
        r'^loc/school/(?P<pk>\d+)/$',
        GetSchoolAPIView.as_view(),
        name='api_get_school'
    ),
    url(
        r'^loc/school/add$',
        AddSchoolAPIView.as_view(),
        name='api_add_school'
    ),
    url(
        r'^loc/school/find$',
        GetSchoolIDAPIView.as_view(),
        name='api_get_school_id'
    ),
    url(
        r'^loc/school/find/fuzzle$',
        GetFuzzleSchoolAPIView.as_view(),
        name='api_get_fuzzle_school'
    ),
    url(
        r'^loc/school/name/(?P<pk>\d+)/$',
        GetSchoolIDNameAPIView.as_view(),
        name='api_get_school_id_name'
    ),
    url(
        r'^loc/school/$',
        GetOrCreateSchoolAPIView.as_view(),
        name='api_get_or_create_school'
    )
]

versioned_api_urlpatterns = [
    url(r'^api/v1/', include(api_urlpatterns, namespace='v1')),
]
urlpatterns = format_suffix_patterns(versioned_api_urlpatterns, allowed=['json'])
