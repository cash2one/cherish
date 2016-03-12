from django.utils.translation import ugettext as _
from rest_framework.exceptions import APIException


class ParameterError(APIException):
    status_code = 400
    default_detail = _('Parameter error')


class OperationError(APIException):
    status_code = 405
    default_detail = _('Operation fail')


