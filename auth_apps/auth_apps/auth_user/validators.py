from django.core import validators
from django.utils.translation import ugettext as _


validate_mobile = validators.RegexValidator(
    r'^[\d]{10,14}$',
    _('Invalid mobile number.'),
    )


validate_phone = validators.RegexValidator(
    r'^[\d-]+$',
    _('Invalid phone number.'),
    )


validate_mobile_code = validators.RegexValidator(
    r'^[\d]{6}$',
    _('Invalid code.'),
    )

validate_username = validators.RegexValidator(
    r'^[\w.@+-]+$',
    _('Enter a valid username. This value may contain only '
      'letters, numbers ' 'and @/./+/-/_ characters.')
    )

username_not_digits = validators.RegexValidator(
    regex=r'^[\d]+$',
    message=_('username cannot be all digits.'),
    code='invalid',
    inverse_match=True
    )
