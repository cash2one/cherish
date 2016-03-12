from __future__ import unicode_literals

from django.contrib.auth import authenticate
from oauth2_provider.oauth2_validators import OAuth2Validator


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
