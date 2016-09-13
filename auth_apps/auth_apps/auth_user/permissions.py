import logging
import socket
import struct
import functools

from django.conf import settings
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

    def has_permission(self, request, view):
        code = request.data.pop('code')
        mobile = request.data.get('mobile')
        if mobile and code:
            logger.debug('[OnceGeneralMobileCodeCheck] mobile:{m}, code:{code}'.format(
                m=mobile, code=code))
            return general_mobile_token_generator.check_token(mobile, code)
        return False


class IPRestriction(permissions.BasePermission):
    message = 'ip invalid'
    net_list = settings.IP_WHITE_LIST

    def has_permission(self, request, view):
        if settings.TEST:
            return True
        ip_addr = request.META['REMOTE_ADDR']
        status = self.check_ip(ip_addr, self.net_list)
        if not status:
            logger.debug('[IPRestriction] ip_addr:{ip}'.format(ip=ip_addr))
            return settings.TEST
        return status

    def check_ip(self, ip, net_list):
        if not (ip and net_list):
            return []
        ip_filter = functools.partial(IPRestriction._addr_in_net, ip)
        return filter(ip_filter, net_list)

    @staticmethod
    def _addr_in_net(ip, net):
        """Is an address in a network"""
        ipaddr = struct.unpack('I', socket.inet_aton(ip))[0]
        net += "/32" if net.find('/') < 0 else ""
        netaddr, bits = net.split('/')
        netmask = struct.unpack('I', socket.inet_aton(netaddr))[0] & ((2L << int(bits)-1) - 1)
        return ipaddr & netmask == netmask
