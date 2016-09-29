from braces.views import LoginRequiredMixin
from django.conf import settings

from .models import TechUUser
from .tasks import xplatform_update_account

class IsOwnerMixin(LoginRequiredMixin):
    """
    This mixin is used to provide an object queryset filtered by the current request.user.
    """
    fields = '__all__'

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


class TechUUserUpdateMixin(object):

    def techu_update(self, user, data):
        if settings.ENABLE_XPLATFORM:
            self._update_to_xplatform(user=user, data=data)

    def _update_to_xplatform(self, user, data):
        if user.source == TechUUser.USER_SOURCE.XPLATFORM and (
            (data.get('mobile') and user.mobile != data['mobile']) or (data.get('username') and user.username != data['username'])
        ):
            xplatform_userid = user.context and user.context.get(u'accountId')
            if xplatform_userid:
                # update account info to xplatform
                xplatform_update_account.delay(
                    userid=xplatform_userid,
                    username=data.get('username'),
                    mobile=data.get('mobile')
                )
