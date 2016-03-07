from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm

from .models import TechUUser


class UserRegisterForm(UserCreationForm):
    error_messages = {
        'email_exist': _('The email already exist in system.'),
        'username_exist': _('Username existed, try another name please.')
    }

    email = forms.EmailField(
        help_text=_('Required. Email Address'), required=True
    )
    birth_date = forms.DateField(
        required=False, widget=forms.SelectDateWidget()
    )

    class Meta:
        model = TechUUser
        fields = [
            'username', 'email', 'birth_date', 'qq', 
            'mobile', 'phone', 'address', 'remark',
        ]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and TechUUser.objects.filter(username=username).exists():
            raise forms.ValidationError(
                self.error_messages['username_exist'],
                code='username_exist',
            )
        return username 

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and TechUUser.objects.filter(email=email).exists():
            raise forms.ValidationError(
                self.error_messages['email_exist'],
                code='email_exist',
            )
        return email



class UserProfileForm(forms.ModelForm):
    # set username and password to read-only
    username = forms.CharField(disabled=True)
    email = forms.EmailField(disabled=True)
    # set birth_date date selector
    birth_date = forms.DateField(
        required=False, widget=forms.SelectDateWidget()
    )

    class Meta:
        model = TechUUser
        fields = [
            'username', 'email', 'birth_date', 'qq', 
            'mobile', 'phone', 'address', 'remark',
        ]

