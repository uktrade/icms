from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.file import FileTarget
from data_migration.models.reference import CommodityGroup
from data_migration.models.user import User

from ..import_application import ImportApplication, ImportApplicationBase


class FirearmBase(ImportApplicationBase):
    class Meta:
        abstract = True

    know_bought_from = models.BooleanField(null=True)
    commodity_group = models.ForeignKey(CommodityGroup, on_delete=models.SET_NULL, null=True)
    commodities_xml = models.TextField(null=True)
    commodities_response_xml = models.TextField(null=True)
    user_import_certs_xml = models.TextField(null=True)
    fa_authorities_xml = models.TextField(null=True)
    bought_from_details_xml = models.TextField(null=True)
    fa_goods_certs_xml = models.TextField(null=True)


class UserImportCertificate(MigrationBase):
    target = models.ForeignKey(FileTarget, on_delete=models.CASCADE)
    import_application = models.ForeignKey(ImportApplication, on_delete=models.CASCADE)
    reference = models.CharField(max_length=200, null=True)
    certificate_type = models.CharField(max_length=200)
    constabulary = models.ForeignKey(
        "data_migration.Constabulary", on_delete=models.PROTECT, null=True
    )
    date_issued = models.DateField(null=True)
    expiry_date = models.DateField(null=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class ImportContact(MigrationBase):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.PROTECT)
    legacy_id = models.IntegerField()
    entity = models.CharField(max_length=20)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200, null=True)
    registration_number = models.CharField(max_length=200, null=True)
    street = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    postcode = models.CharField(max_length=200, null=True)
    region = models.CharField(max_length=200, null=True)
    country = models.ForeignKey(
        "data_migration.Country", on_delete=models.PROTECT, related_name="+"
    )
    dealer = models.CharField(max_length=10, null=True)
    created_datetime = models.DateTimeField()
    updated_datetime = models.DateTimeField(auto_now=True)


class SupplementaryInfoBase(MigrationBase):
    class Meta:
        abstract = True

    is_complete = models.BooleanField(default=False)
    completed_datetime = models.DateTimeField(null=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    no_report_reason = models.CharField(
        max_length=4000,
        null=True,
    )
    supplementary_report_xml = models.TextField(null=True)


class SupplementaryReportBase(MigrationBase):
    class Meta:
        abstract = True

    transport = models.CharField(max_length=4, null=True)
    date_received = models.DateField(null=True)
    bought_from_legacy_id = models.IntegerField(null=True)
    created = models.DateTimeField(null=True)
    report_firearms_xml = models.TextField(null=True)


class SupplementaryReportFirearmBase(MigrationBase):
    class Meta:
        abstract = True

    serial_number = models.CharField(max_length=400, null=True)
    calibre = models.CharField(max_length=400, null=True)
    model = models.CharField(max_length=400, null=True)
    proofing = models.CharField(max_length=3, null=True, default=None)
    is_manual = models.BooleanField(default=False)
    is_upload = models.BooleanField(default=False)
    is_no_firearm = models.BooleanField(default=False)
    goods_certificate_legacy_id = models.PositiveIntegerField(null=True)
