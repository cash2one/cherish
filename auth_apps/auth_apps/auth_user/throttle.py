# -*- coding: utf-8 -*-

from rest_framework import throttling


class BackendAPIThrottle(throttling.BaseThrottle):
    def allow_request(self, request, view):
        return True
