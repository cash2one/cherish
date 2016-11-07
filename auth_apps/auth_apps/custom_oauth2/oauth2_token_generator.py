# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from oauthlib import common
from oauth2_provider.models import AccessToken


def techu_token_generator(request, refresh_token=False):
    access_token = AccessToken.objects.filter(user=request.user,
                                              application=request.client).order_by('-id').first()
    if access_token:
        return access_token.token
    return common.generate_token()
