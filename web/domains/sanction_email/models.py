from django.db import models


class SanctionEmail(models.Model):
    is_active = models.BooleanField(default=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(verbose_name="Email Address", max_length=254)

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
