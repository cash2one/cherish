import logging

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.views.generic.base import TemplateView

from .models import AuthUser
from .forms import UserBasicForm, UserProfileForm, UserReadOnlyBasicForm

logger = logging.getLogger(__name__)


class HomePageView(TemplateView):
    template_name = 'home.html'


class UserRegisterView(View):
    user_form_class = UserBasicForm
    profile_form_class = UserProfileForm
    template_name = 'registration/register.html'

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        user_form = self.user_form_class()
        profile_form = self.profile_form_class()
        return render(request, self.template_name, {
            'user_form': user_form, 
            'profile_form': profile_form,
        })

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @method_decorator(transaction.atomic)
    def post(self, request, *args, **kwargs):
        user_form = self.user_form_class(data=request.POST)
        profile_form = self.profile_form_class(data=request.POST)
        if all((user_form.is_valid(), profile_form.is_valid())):
            # add new user
            user = user_form.save()
            auth_user = profile_form.save(commit=False)
            auth_user.user = user
            auth_user.save()
            logger.info('[ADD USER] {user}'.format(user=user))
            return HttpResponseRedirect(reverse('register_done'))

        return render(request, self.template_name, {
            'user_form': user_form, 
            'profile_form': profile_form,
        })


class UserRegisterDoneView(View):
    template_name = 'registration/register_done.html'
    
    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class UserProfileView(View):
    user_form_class = UserReadOnlyBasicForm
    profile_form_class = UserProfileForm
    template_name = 'registration/profile.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        auth_user = AuthUser.objects.get(user=request.user)
        assert(auth_user)
        user_form = self.user_form_class(instance=auth_user.user)
        profile_form = self.profile_form_class(instance=auth_user)
        return render(request, self.template_name, {
            'user_form': user_form, 
            'profile_form': profile_form,
        })

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        auth_user = AuthUser.objects.get(user=request.user)
        assert(auth_user)
        user_form = self.user_form_class(instance=auth_user.user)
        profile_form = self.profile_form_class(
            data=request.POST, instance=auth_user)
        message = None
        if profile_form.is_valid():
            # add new user
            profile_form.save()
            message = 'profile updated !'

        return render(request, self.template_name, {
            'message': message,
            'user_form': user_form, 
            'profile_form': profile_form,
        })

