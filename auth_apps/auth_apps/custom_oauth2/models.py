from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from oauth2_provider.validators import validate_uris
from oauth2_provider.models import AbstractApplication


class TechUApplication(AbstractApplication):
    notify_uris = models.TextField(
        help_text=_('Notify callback URIs list, space separated'),
        validators=[validate_uris], blank=True)

    @property
    def default_notify_uri(self):
        """
        Returns the default notify_uri extracting the first item from
        the :attr:`notify_uris` string
        """
        if self.notify_uris:
            return self.notify_uris.split().pop(0)
