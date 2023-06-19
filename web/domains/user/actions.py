from django.contrib import messages

from web.views.actions import PostAction

from .models import User


class ActivateUser(PostAction):
    action = "activate"
    label = "Activate"
    confirm = True
    confirm_message = "Are you sure you want to activate this account?"
    icon = "icon-eye"

    def display(self, user):
        return not user.is_active

    def handle(self, request, view, *args, **kwargs):
        user: User = self._get_item(request, view.model)
        user.is_active = True
        user.save()
        messages.success(request, "Account activated successfully")


class DeactivateUser(PostAction):
    action = "block"
    label = "Deactivate"
    confirm = True
    confirm_message = "Are you sure you want to deactivate this account?"
    icon = "icon-eye-blocked"

    def display(self, user):
        return user.is_active

    def handle(self, request, view, *args, **kwargs):
        user: User = self._get_item(request, view.model)
        user.is_active = False
        user.save()

        messages.success(request, "Account deactivated successfully")
