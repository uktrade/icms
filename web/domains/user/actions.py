from django.urls import reverse

from web.models import User
from web.views.actions import LinkAction


class ActivateUser(LinkAction):
    label = "Activate"
    icon = "icon-eye"

    def display(self, user: User) -> bool:
        return not user.is_active

    def href(self, user: User) -> str:
        return reverse("user-reactivate", kwargs={"user_pk": user.pk})


class DeactivateUser(LinkAction):
    label = "Deactivate"
    icon = "icon-eye-blocked"

    def display(self, user: User) -> bool:
        return user.is_active

    def href(self, user: User) -> str:
        return reverse("user-deactivate", kwargs={"user_pk": user.pk})
