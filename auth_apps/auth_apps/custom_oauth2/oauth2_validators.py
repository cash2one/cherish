from __future__ import unicode_literals

import logging
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import authenticate
from oauth2_provider.oauth2_validators import OAuth2Validator
from oauth2_provider.models import AccessToken, RefreshToken
from oauth2_provider.settings import oauth2_settings


logger = logging.getLogger(__name__)


class TechUOAuth2Validator(OAuth2Validator):
    # override
    def validate_user(self, username, password, client, request, *args, **kwargs):
        """
        Check username and password correspond to a valid and active User
        """
        u = authenticate(identity=username, password=password)
        if u is not None and u.is_active:
            request.user = u
            return True
        return False

    # override
    def save_bearer_token(self, token, request, *args, **kwargs):
        if request.refresh_token:
            # remove used refresh token
            try:
                RefreshToken.objects.get(token=request.refresh_token).revoke()
            except RefreshToken.DoesNotExist:
                assert()  # TODO though being here would be very strange, at least log the error

        expires = timezone.now() + timedelta(seconds=oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        if request.grant_type == 'client_credentials':
            request.user = None

        access_token = AccessToken.objects.filter(user=request.user,
                                                  application=request.client).order_by('-id').first()

        if access_token:
            access_token.expires = expires
        else:
            access_token = AccessToken(
                user=request.user,
                scope=token['scope'],
                expires=expires,
                token=token['access_token'],
                application=request.client)
            access_token.save()

        if not access_token.pk and 'refresh_token' in token:
            refresh_token = RefreshToken(
                user=request.user,
                token=token['refresh_token'],
                application=request.client,
                access_token=access_token
            )
            refresh_token.save()

        # TODO check out a more reliable way to communicate expire time to oauthlib
        token['expires_in'] = oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS
