from django.db import models

from web.domains.user.models import User


class SIGLTransmission(models.Model):
    transmission_type = models.CharField(max_length=12)
    status = models.CharField(max_length=8)
    request_type = models.CharField(max_length=8)
    sent_datetime = models.DateTimeField()
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
    response_datetime = models.DateTimeField(null=True)
    response_message = models.CharField(max_length=120, null=True)
    response_code = models.IntegerField(null=True)
