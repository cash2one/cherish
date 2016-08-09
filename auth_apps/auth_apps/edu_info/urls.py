from django.conf.urls import url, include
from rest_framework.urlpatterns import format_suffix_patterns

from .views import GetSchoolAPIView, GetSchoolIDNameAPIView


api_urlpatterns = [
    url(
        r'^loc/school/(?P<pk>\d+)/$',
        GetSchoolAPIView.as_view(),
        name='api_get_school'
    ),
    url(
        r'^loc/school/name/(?P<pk>\d+)/$',
        GetSchoolIDNameAPIView.as_view(),
        name='api_get_school_id_name'
    ),
]

versioned_api_urlpatterns = [
    url(r'^api/v1/', include(api_urlpatterns, namespace='v1')),
]
urlpatterns = format_suffix_patterns(versioned_api_urlpatterns, allowed=['json'])
