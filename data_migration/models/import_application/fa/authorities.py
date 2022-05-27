from typing import Generator

from django.db import models
from django.db.models import OuterRef, Subquery

from data_migration.models.base import MigrationBase
from data_migration.models.file import File, FileTarget
from data_migration.models.reference import Constabulary
from data_migration.models.user import Importer, Office, User


class FirearmsAuthority(MigrationBase):
    is_active = models.BooleanField(null=False, default=True)
    reference = models.CharField(max_length=100, null=True)
    certificate_type = models.CharField(max_length=20, null=True)
    postcode = models.CharField(max_length=30, null=True)
    address = models.CharField(max_length=300, null=True)
    address_entry_type = models.CharField(max_length=10, null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    further_details = models.CharField(max_length=4000, null=True)
    issuing_constabulary = models.ForeignKey(Constabulary, on_delete=models.PROTECT, null=True)
    importer = models.ForeignKey(Importer, on_delete=models.PROTECT, null=False)
    act_quantity_xml = models.TextField(null=True)
    file_target_xml = models.TextField(null=True)


class FirearmsAct(MigrationBase):
    act = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    updated_datetime = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+", null=True)


class ActQuantity(MigrationBase):
    firearmsauthority = models.ForeignKey(FirearmsAuthority, on_delete=models.PROTECT)
    firearmsact = models.ForeignKey(FirearmsAct, on_delete=models.PROTECT)
    quantity = models.IntegerField(null=True)
    infinity = models.BooleanField(default=False)


class FirearmsAuthorityOffice(MigrationBase):
    firearmsauthority = models.ForeignKey(FirearmsAuthority, on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.CASCADE)


class FirearmsAuthorityFile(MigrationBase):
    firearmsauthority = models.ForeignKey(FirearmsAuthority, on_delete=models.CASCADE)
    filetarget = models.ForeignKey(FileTarget, on_delete=models.CASCADE)

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        sub_query = File.objects.filter(target_id=OuterRef("filetarget_id"))

        return (
            cls.objects.select_related("target")
            .prefetch_related("target__files")
            .annotate(
                file_id=Subquery(sub_query.values("pk")[:1]),
            )
            .exclude(file_id__isnull=True)
            .values("id", "firearmsauthority_id", "file_id")
            .iterator()
        )


class Section5Authority(MigrationBase):
    is_active = models.BooleanField(null=False, default=True)
    reference = models.CharField(max_length=100, null=True)
    postcode = models.CharField(max_length=30, null=True)
    address = models.CharField(max_length=300, null=True)
    address_entry_type = models.CharField(max_length=10, null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    further_details = models.CharField(max_length=4000, null=True)
    importer = models.ForeignKey(Importer, on_delete=models.PROTECT, null=False)
    clause_quantity_xml = models.TextField(null=True)
    file_target_xml = models.TextField(null=True)


class Section5Clause(MigrationBase):
    clause = models.CharField(max_length=100)
    legacy_code = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    updated_datetime = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+", null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["legacy_code"]


class ClauseQuantity(MigrationBase):
    section5authority = models.ForeignKey(Section5Authority, on_delete=models.PROTECT)
    section5clause = models.ForeignKey(Section5Clause, on_delete=models.PROTECT)
    quantity = models.IntegerField(null=True)
    infinity = models.BooleanField(default=False)


class Section5AuthorityOffice(MigrationBase):
    section5authority = models.ForeignKey(FirearmsAuthority, on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.CASCADE)


class Section5AuthorityFile(MigrationBase):
    section5authority = models.ForeignKey(FirearmsAuthority, on_delete=models.CASCADE)
    filetarget = models.ForeignKey(FileTarget, on_delete=models.CASCADE)

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        sub_query = File.objects.filter(target_id=OuterRef("filetarget_id"))

        return (
            cls.objects.select_related("target")
            .prefetch_related("target__files")
            .annotate(
                file_id=Subquery(sub_query.values("pk")[:1]),
            )
            .exclude(file_id__isnull=True)
            .values("id", "section5authority_id", "file_id")
            .iterator()
        )
