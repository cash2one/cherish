import logging

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db import transaction
from django.views.generic.base import TemplateView
from django.contrib.auth.models import Group
from rest_framework import permissions, generics
from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope

from .models import TechUUser
from .forms import UserProfileForm, UserRegisterForm
from .serializers import TechUUserSerializer, GroupSerializer
from .permissions import IsTokenOwnerPermission

logger = logging.getLogger(__name__)


class HomePageView(TemplateView):
    template_name = 'home.html'


class UserRegisterView(View):
    form_class = UserRegisterForm
    template_name = 'accounts/register.html'

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {
            'form': form, 
        })

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    @method_decorator(transaction.atomic)
    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        if form.is_valid():
            # add new user
            user = form.save()
            logger.info('[ADD USER] {user}'.format(user=user))
            return HttpResponseRedirect(reverse('register_done'))

        return render(request, self.template_name, {
            'form': form, 
        })


class UserRegisterDoneView(View):
    template_name = 'accounts/register_done.html'
    
    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class UserProfileView(View):
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        auth_user = TechUUser.objects.get(pk=request.user.pk)
        assert(auth_user)
        form = self.form_class(instance=auth_user)
        return render(request, self.template_name, {
            'form': form, 
        })

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        auth_user = TechUUser.objects.get(pk=request.user.pk)
        assert(auth_user)
        form = self.form_class(instance=auth_user)
        message = None
        if form.is_valid():
            # add new user
            form.save()
            message = 'profile updated !'

        return render(request, self.template_name, {
            'message': message,
            'form': form,
        })


class UserRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [
        permissions.IsAuthenticated, TokenHasScope, IsTokenOwnerPermission
    ]
    required_scopes = ['user']
    queryset = TechUUser.objects.all()
    serializer_class = TechUUserSerializer


class GroupRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [
        permissions.IsAuthenticated, TokenHasScope, IsTokenOwnerPermission
    ]
    required_scopes = ['group']
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

