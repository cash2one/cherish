import logging

from rest_framework import permissions

logger = logging.getLogger(__name__)


class IsTokenOwnerPermission(permissions.BasePermission):
    message = 'Not resource owner.'

    def has_object_permission(self, request, view, obj):
        if request.user:
            logger.debug('[IsTokenOwnerPermission] token user(request.user): {user}'.format(
                user=request.user))
            return (obj == request.user)
        return False
