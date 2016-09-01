from braces.views import LoginRequiredMixin


class IsOwnerMixin(LoginRequiredMixin):
    """
    This mixin is used to provide an object queryset filtered by the current request.user.
    """
    fields = '__all__'

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)


