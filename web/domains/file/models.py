from django.db import models
from web.domains.user.models import User


class File(models.Model):
    is_active = models.BooleanField(blank=False, null=False, default=True)
    filename = models.CharField(max_length=300, blank=False, null=True)
    content_type = models.CharField(max_length=100, blank=False, null=True)
    browser_content_type = models.CharField(max_length=100,
                                            blank=False,
                                            null=True)
    description = models.CharField(max_length=300, blank=True, null=True)
    file_size = models.IntegerField(blank=False, null=True)
    path = models.CharField(max_length=4000, blank=True, null=True)
    error_message = models.CharField(max_length=4000, blank=True, null=True)
    created_datetime = models.DateTimeField(auto_now_add=True,
                                            blank=False,
                                            null=True)
    created_by = models.ForeignKey(User,
                                   on_delete=models.PROTECT,
                                   blank=False,
                                   null=True)
