# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from oauthlib import common
from oauth2_provider.models import AccessToken


def techu_token_generator(request, refresh_token=False):
    access_tokens = AccessToken.objects.filter(user=request.user,
                                               application=request.client).order_by('-id')
    if access_tokens:
        return access_tokens[0].token
    return common.generate_token()
