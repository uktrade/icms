import uuid

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from web.types import TypedTextChoices


class ECILUserExportApplication(models.Model):
    """Model to store temporary data before the real export application model is created.

    To get around the constraint of not breaking V2 while we iterate ECIL.
    There is only ever one record per user in the system.
    """

    class ExportApplicationsChoices(TypedTextChoices):
        CFS = ("cfs", "Certificate of Free Sale (CFS)")
        COM = ("com", "Certificate of Manufacture (CoM)")
        GMP = ("gmp", "Certificate of Good Manufacturing Practice (CGMP)")

    app_type = models.CharField(max_length=3, choices=ExportApplicationsChoices.choices, default="")

    created_by = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )

    exporter = models.ForeignKey(
        "web.Exporter", on_delete=models.CASCADE, related_name="+", null=True
    )
    exporter_office = models.ForeignKey(
        "web.Office", on_delete=models.CASCADE, related_name="+", null=True
    )
    agent = models.ForeignKey("web.Exporter", on_delete=models.CASCADE, related_name="+", null=True)
    agent_office = models.ForeignKey(
        "web.Office", on_delete=models.CASCADE, related_name="+", null=True
    )


class ECILExample(models.Model):
    class PrimaryColours(TypedTextChoices):
        blue = ("blue", "Blue")
        red = ("red", "Red")
        yellow = ("yellow", "Yellow")

    big_integer_field = models.BigIntegerField(
        verbose_name="Big integer field", help_text="Enter a value"
    )
    editable_binary_field = models.BinaryField(
        verbose_name="Editable binary field",
        help_text="Enter a value",
        max_length=255,
        editable=True,
    )
    readonly_binary_field = models.BinaryField(
        verbose_name="Readonly Binary field",
        help_text="Enter a value",
        default=b"example value",
        editable=False,
    )
    boolean_field = models.BooleanField(
        verbose_name="Boolean field",
        help_text="Enter a value",
    )
    optional_boolean_field = models.BooleanField(
        verbose_name="Optional Boolean field", help_text="Enter a value", null=True
    )
    char_field = models.CharField(
        verbose_name="Char field", help_text="Enter a value", max_length=255
    )
    char_choice_field = models.CharField(
        verbose_name="Char choice field",
        help_text="Pick a colour",
        choices=PrimaryColours.choices,
        max_length=6,
        null=True,
    )
    optional_char_field = models.CharField(
        verbose_name="Optional Char field",
        help_text="Enter a value",
        max_length=255,
        blank=True,
    )
    date_field = models.DateField(
        verbose_name="Date field",
        help_text="Enter a value",
    )
    datetime_field = models.DateTimeField(
        verbose_name="Datetime field",
        help_text="Enter a value",
    )
    decimal_field = models.DecimalField(
        verbose_name="Decimal field", help_text="Enter a value", max_digits=5, decimal_places=2
    )
    duration_field = models.DurationField(
        verbose_name="Duration field",
        help_text="Enter a value",
    )
    email_field = models.EmailField(
        verbose_name="Email field",
        help_text="Enter a value",
    )
    #
    # Won't use this
    # file_field = models.FileField()
    #
    # Won't use this
    # file_path_field = models.FilePathField()
    float_field = models.FloatField(
        verbose_name="Float field",
        help_text="Enter a value",
    )
    foreign_key_field = models.ForeignKey(
        verbose_name="Foreign key field",
        help_text="Enter a value",
        to="web.Commodity",
        related_name="+",
        on_delete=models.CASCADE,
    )
    #
    # Won't use this
    # image_field = models.ImageField()
    integer_field = models.IntegerField(
        verbose_name="Integer field",
        help_text="Enter a value",
    )
    ip_address_field = models.GenericIPAddressField(
        verbose_name="IP Address field",
        help_text="Enter a value",
    )
    json_field = models.JSONField(
        verbose_name="Foo", help_text="Enter a value", encoder=DjangoJSONEncoder
    )
    many_to_many_field = models.ManyToManyField(
        verbose_name="JSON field",
        help_text="Enter a value",
        to="web.CommodityGroup",
        related_name="+",
    )
    positive_big_integer_field = models.PositiveBigIntegerField(
        verbose_name="Positive big integer field",
        help_text="Enter a value",
    )
    positive_integer_field = models.PositiveIntegerField(
        verbose_name="Positive integer field",
        help_text="Enter a value",
    )
    positive_small_integer_field = models.PositiveSmallIntegerField(
        verbose_name="Positive small integer field",
        help_text="Enter a value",
    )
    slug_field = models.SlugField(
        verbose_name="Slug field",
        help_text="Enter a value",
    )
    small_integer_field = models.SmallIntegerField(
        verbose_name="Small Integer field",
        help_text="Enter a value",
    )
    text_field = models.TextField(
        verbose_name="Text field", help_text="Enter a value", max_length=4096
    )
    time_field = models.TimeField(
        verbose_name="Time field",
        help_text="Enter a value",
    )
    url_field = models.URLField(
        verbose_name="URL field",
        help_text="Enter a value",
    )
    uuid_field = models.UUIDField(
        verbose_name="UUID field", help_text="Enter a value", default=uuid.uuid4, editable=True
    )

    def __str__(self):
        fields = [
            "big_integer_field",
            "boolean_field",
            "optional_boolean_field",
            "char_field",
            "char_choice_field",
            "optional_char_field",
            "date_field",
            "decimal_field",
            "email_field",
            "float_field",
            "integer_field",
            "positive_big_integer_field",
            "positive_integer_field",
            "positive_small_integer_field",
            "slug_field",
            "small_integer_field",
            "text_field",
            "foreign_key_field",
        ]
        model_repr = ", ".join(f"{f}={getattr(self, f)}" for f in fields)

        return f"ECILExample(pk={self.pk}, {model_repr})"


class ECILMultiStepExample(models.Model):
    class PrimaryColours(TypedTextChoices):
        blue = ("blue", "Blue")
        red = ("red", "Red")
        yellow = ("yellow", "Yellow")

    # editable fields
    favourite_colour = models.CharField(
        verbose_name="What's your favourite primary colour",
        help_text="Pick a colour",
        choices=PrimaryColours.choices,
        max_length=6,
    )
    likes_cake = models.BooleanField(
        verbose_name="Do you like cake?",
        help_text="Enter a value",
    )
    favourite_book = models.CharField(
        verbose_name="Favourite book", help_text="Enter a value", max_length=255
    )

    def __str__(self):
        return (
            f"ECILMultiStepExample(pk={self.pk}, favourite_colour={self.favourite_colour}, "
            f"likes_cake={self.likes_cake}, favourite_book={self.favourite_book})"
        )

    # auto fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
