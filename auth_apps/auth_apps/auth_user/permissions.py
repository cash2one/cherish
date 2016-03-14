import logging

from rest_framework import permissions

from .tokens import user_mobile_token_generator, general_mobile_token_generator

logger = logging.getLogger(__name__)


class IsTokenOwnerPermission(permissions.BasePermission):
    message = 'Not resource owner.'

    def has_object_permission(self, request, view, obj):
        if request.user:
            logger.debug('[IsTokenOwnerPermission] token user(request.user): {user}'.format(
                user=request.user))
            return (obj == request.user)
        return False


class OnceUserMobileCodeCheck(permissions.BasePermission):
    """
        NOTICE: login required !!
    """
    message = 'mobile code invalid'

    def has_object_permission(self, request, view, obj):
        code = request.data.pop('code')
        if request.user and code:
            logger.debug('[OnceUserMobileCodeCheck] user: {user}'.format(
                user=request.user))
            return user_mobile_token_generator.check_token(request.user, code)
        return False


class OnceGeneralMobileCodeCheck(permissions.BasePermission):
    """
        NOTICE: general one, no login requirement
    """
    message = 'mobile code invalid'

    def has_object_permission(self, request, view, obj):
        code = request.data.pop('code')
        mobile = request.data.get('mobile')
        if mobile and code:
            logger.debug('[OnceGeneralMobileCodeCheck] mobile:{m}, code:{code}'.format(
                m=mobile, code=code))
            return general_mobile_token_generator.check_token(mobile, code)
        return False

