from typing import TYPE_CHECKING

from django.db import models
from django.db.models import QuerySet

from .types import CountryGroupName

if TYPE_CHECKING:
    from web.models import Country


class CountryMangerBase(models.Manager):
    def _get_country_group_countries(self, name: CountryGroupName) -> QuerySet["Country"]:
        return self.get_queryset().filter(country_groups__name__iexact=name, is_active=True)


class ApplicationCountryManager(CountryMangerBase):
    """Custom Country manager to fetch countries used in specific applications."""

    #
    # Export Applications
    #
    def get_cfs_countries(self) -> QuerySet["Country"]:
        """Get Certificate of Free Sale countries.

        DB Field: CertificateOfFreeSaleApplication.countries
        """

        return self._get_country_group_countries(CountryGroupName.CFS)

    def get_cfs_com_countries(self) -> QuerySet["Country"]:
        """Get Certificate of Free Sale country of manufacture countries.

        DB Field: CFSSchedule.country_of_manufacture
        """

        return self._get_country_group_countries(CountryGroupName.CFS_COM)

    def get_com_countries(self) -> QuerySet["Country"]:
        """Get Certificate of Manufacture countries.

        DB Field: CertificateOfManufactureApplication.countries
        """

        return self._get_country_group_countries(CountryGroupName.COM)

    def get_gmp_countries(self) -> QuerySet["Country"]:
        """Get Certificate of Good Manufacturing Practice countries.

        DB Field: CertificateOfGoodManufacturingPracticeApplication.countries
        """

        return self._get_country_group_countries(CountryGroupName.GMP)

    #
    # Import Applications
    #
    def get_fa_dfl_issuing_countries(self) -> QuerySet["Country"]:
        """Get FA-DFL issuing countries.

        DB Field: DFLGoodsCertificate.issuing_country
        """

        return self._get_country_group_countries(CountryGroupName.FA_DFL_IC)

    def get_fa_oil_coc_countries(self) -> QuerySet["Country"]:
        """Get FA-OIL consignment countries.

        DB Field: OpenIndividualLicenceApplication.consignment_country
        """

        return self._get_country_group_countries(CountryGroupName.FA_OIL_COC)

    def get_fa_oil_coo_countries(self) -> QuerySet["Country"]:
        """Get FA-OIL origin countries.

        DB Field: OpenIndividualLicenceApplication.origin_country
        """

        return self._get_country_group_countries(CountryGroupName.FA_OIL_COO)

    def get_fa_sil_coc_countries(self) -> QuerySet["Country"]:
        """Get FA-SIL consignment countries.

        DB Field: SILApplication.consignment_country
        """

        return self._get_country_group_countries(CountryGroupName.FA_SIL_COC)

    def get_fa_sil_coo_countries(self) -> QuerySet["Country"]:
        """Get FA-SIL origin countries.

        DB Field: SILApplication.origin_country
        """

        return self._get_country_group_countries(CountryGroupName.FA_SIL_COO)

    def get_sanctions_coo_and_coc_countries(self) -> QuerySet["Country"]:
        """Get Sanctions origin and consignment countries.

        DB Field: SanctionsAndAdhocApplication.origin_country
        DB Field: SanctionsAndAdhocApplication.consignment_country
        """

        return self._get_country_group_countries(CountryGroupName.SANCTIONS_COC_COO)

    # TODO: ICMSLST-2666 Use when refactoring form logic.
    def get_sanctions_countries(self) -> QuerySet["Country"]:
        """Get Sanctions countries."""

        return self._get_country_group_countries(CountryGroupName.SANCTIONS)

    def get_wood_countries(self) -> QuerySet["Country"]:
        """Get Wood countries."""

        return self._get_country_group_countries(CountryGroupName.WOOD_COO)

    #
    # Inactive Import Applications
    #
    def get_iron_coo_countries(self) -> QuerySet["Country"]:
        """Get Iron & Steel origin countries.

        DB Field: IronSteelApplication.origin_country
        """

        return self._get_country_group_countries(CountryGroupName.IRON)

    def get_opt_coo_countries(self) -> QuerySet["Country"]:
        """Get OPT origin countries / processing countries.

        DB Field: OutwardProcessingTradeApplication.cp_origin_country
        DB Field: OutwardProcessingTradeApplication.cp_processing_country
        """

        return self._get_country_group_countries(CountryGroupName.OPT_COO)

    def get_opt_temp_export_coo_countries(self) -> QuerySet["Country"]:
        """Get OPT origin countries / processing countries.

        DB Field: OutwardProcessingTradeApplication.teg_origin_country
        """

        return self._get_country_group_countries(CountryGroupName.OPT_TEMP_EXPORT_COO)

    def get_textiles_coo_countries(self) -> QuerySet["Country"]:
        """Get Textiles origin countries

        DB Field: TextilesApplication.origin_country
        """

        return self._get_country_group_countries(CountryGroupName.TEXTILES_COO)

    def get_derogations_coo_countries(self) -> QuerySet["Country"]:
        return self._get_country_group_countries(CountryGroupName.DEROGATION_FROM_SANCTION_COO)


class UtilityCountryManager(CountryMangerBase):
    """Custom Country manager to fetch specific application wide country groups."""

    def get_all_countries(self) -> QuerySet["Country"]:
        """Return all active countries."""
        return self.get_queryset().filter(is_active=True, type=self.model.SOVEREIGN_TERRITORY)

    def get_eu_countries(self) -> QuerySet["Country"]:
        return self._get_country_group_countries(CountryGroupName.EU)

    def get_non_eu_countries(self) -> QuerySet["Country"]:
        return self._get_country_group_countries(CountryGroupName.NON_EU)
