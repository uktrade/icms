from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models

from web.models.shared import YesNoChoices
from web.types import TypedTextChoices


class UserFeedbackSurvey(models.Model):
    class SatisfactionLevel(TypedTextChoices):
        VERY_DISSATISIFED = ("VERY_DISSATISFIED", "Very dissatisfied")
        DISSATISIFED = ("DISSATISFIED", "Dissatisfied")
        NEITHER = ("NEITHER", "Neither dissatisfied or satisfied")
        SATISFIED = ("SATISFIED", "Satisfied")
        VERY_SATISFIED = ("VERY_SATISFIED", "Very satisfied")

    class EaseFindChoices(TypedTextChoices):
        VERY_EASY = ("VERY_EASY", "Very Easy")
        EASY = ("EASY", "Easy")
        NEITHER = ("NEITHER", "Neither easy or difficult")
        DIFFICULT = ("DIFFICULT", "Difficult")
        VERY_DIFFICULT = ("VERY_DIFFICULT", "Very difficult")

    class AdditionalSupportChoices(TypedTextChoices):
        NO = ("NO", "No, I didn’t need any additional support ")
        EMAILED = ("EMAILED", "Yes, I emailed asking for additional support")
        COULD_NOT_FIND = ("COULD_NOT_FIND", "Yes, but I could not find any additional support")
        DONT_KNOW = ("DONT_KNOW", "I don’t know ")

    class IssuesChoices(TypedTextChoices):
        UNABLE_TO_FIND = ("UNABLE_TO_FIND", "I did not find what I was looking for")
        NAVIGATION = ("NAVIGATION", "I found it difficult to navigate the service")
        LACKS_FEATURE = ("LACKS_FEATURE", "The service lacks a feature I need")
        UNABLE_TO_LOAD = ("UNABLE_TO_LOAD", "I was not able to load, refresh, or enter a page")
        OTHER = ("OTHER", "Other")
        NO = ("NO", "I did not experience any issues")

    satisfaction = models.CharField(
        max_length=18,
        choices=SatisfactionLevel,
        verbose_name="Overall satisfaction with the service",
    )
    issues = ArrayField(
        models.CharField(max_length=16, choices=IssuesChoices),
        default=list,
        blank=True,
        verbose_name="Did you experience any of the following issues?",
    )
    issue_details = models.TextField(
        blank=True,
        default="",
        verbose_name="Tell us more about the issue you had.",
    )
    find_service = models.CharField(
        max_length=16,
        choices=EaseFindChoices,
        verbose_name="How was the process of finding the service?",
        default="",
        blank=True,
    )
    find_service_details = models.TextField(
        default="", blank=True, verbose_name="Tell us why the service was not easy to find."
    )
    additional_support = models.CharField(
        max_length=16,
        choices=AdditionalSupportChoices,
        verbose_name="Did you need any additional support at any point during the application?",
        default="",
        null=True,
    )
    service_improvements = models.TextField(
        blank=True, default="", verbose_name="How could we improve the service?"
    )
    future_contact = models.CharField(
        max_length=3,
        choices=YesNoChoices,
        verbose_name="Would you be happy for us to contact you in the future to help us improve the service?",
        blank=True,
        default="",
    )
    referrer_path = models.CharField(max_length=255, blank=True, default="")
    site = models.CharField(max_length=60)
    process = models.ForeignKey("web.Process", on_delete=models.PROTECT, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_datetime = models.DateTimeField(auto_now_add=True)
