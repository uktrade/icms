from django.db import models

from web.domains.case._import.models import ChecklistBase
from web.domains.commodity.models import Commodity
from web.domains.country.models import Country
from web.domains.file.models import File
from web.flow.models import ProcessTypes
from web.models.shared import YesNoChoices, YesNoNAChoices, at_least_0

from ..models import ImportApplication

_ONCE_PER_YEAR = """This question only needs to be completed once per year. If
you have already completed this question on a previous application this year,
you may select 'N/A'.""".replace(
    "\n", " "
)

CP_CATEGORIES = ["4", "5", "6", "7", "8", "15", "21", "24", "26", "27", "29", "73"]
_CP_CATEGORY_CHOICES = [(x, x) for x in CP_CATEGORIES]


class OutwardProcessingTradeFile(File):
    class Type(models.TextChoices):
        SUPPORTING_DOCUMENT = ("supporting_document", "Supporting Documents")
        FQ_EMPLOYMENT_DECREASED = ("fq_employment_decreased", "Statistics")
        FQ_PRIOR_AUTHORISATION = ("fq_prior_authorisation", "Copy of Prior Authorisation")
        FQ_PAST_BENEFICIARY = ("fq_past_beneficiary", "Justification")
        FQ_NEW_APPLICATION = ("fq_new_application", "Justification")
        FQ_FURTHER_AUTHORISATION = ("fq_further_authorisation", "Evidence/Past Correspondence")
        FQ_SUBCONTRACT_PRODUCTION = ("fq_subcontract_production", "Declaration from Subcontractor")

    file_type = models.CharField(max_length=32, choices=Type.choices)


class OutwardProcessingTradeApplication(ImportApplication):
    PROCESS_TYPE = ProcessTypes.OPT

    customs_office_name = models.CharField(
        max_length=100, null=True, verbose_name="Requested customs supervising office name"
    )

    customs_office_address = models.TextField(
        max_length=4000, null=True, verbose_name="Requested customs supervising office address"
    )

    rate_of_yield = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        verbose_name="Rate of yield (kg per garment)",
        validators=[at_least_0],
    )

    rate_of_yield_calc_method = models.TextField(
        max_length=4000, blank=True, null=True, verbose_name="Rate of yield calculation method"
    )

    last_export_day = models.DateField(
        null=True,
        verbose_name="Last Export Day",
        help_text="Requested last day of authorised exportation.",
    )

    reimport_period = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        verbose_name="Period for re-importation (months)",
        validators=[at_least_0],
    )

    nature_process_ops = models.TextField(
        max_length=4000, null=True, verbose_name="Nature of processing operations"
    )

    suggested_id = models.TextField(
        max_length=4000,
        null=True,
        verbose_name="Suggested means of identification",
        help_text="Enter the suggested means of identification of re-imported compensating products.",
    )

    # Compensating Products fields (cp_ prefix)
    cp_origin_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Country Of Origin",
        help_text="Select the country that the compensating products originate from.",
    )

    cp_processing_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Country Of Processing",
        help_text="Select the country that the compensating products were processed in.",
    )

    cp_category = models.CharField(
        null=True,
        max_length=2,
        choices=_CP_CATEGORY_CHOICES,
        verbose_name="Category",
        help_text="The category defines what commodities you are applying to import.",
    )

    cp_category_licence_description = models.CharField(
        null=True,
        max_length=4000,
        verbose_name="Category Description",
        help_text=(
            "By default, this is the category description. You may need to"
            " alter the description to a shorter form in order for it to"
            " display correctly on the licence."
        ),
    )

    cp_total_quantity = models.DecimalField(
        null=True,
        max_digits=9,
        decimal_places=2,
        verbose_name="Total Quantity",
        validators=[at_least_0],
        help_text=(
            "Please note that maximum allocations apply. Please check the"
            " guidance to ensure that you do not apply for more than is allowable."
        ),
    )

    cp_total_value = models.DecimalField(
        null=True,
        max_digits=9,
        decimal_places=2,
        verbose_name="Total Value (Euro)",
        validators=[at_least_0],
        help_text="Value of processing of the fabric/yarn",
    )

    cp_commodities = models.ManyToManyField(
        Commodity,
        related_name="+",
        verbose_name="Commodity Code",
        help_text=(
            "It is the responsibility of the applicant to ensure that the"
            " commodity code in this box is correct. If you are unsure of"
            " the correct commodity code, consult the HM Revenue and Customs"
            " Integrated Tariff Book, Volume 2, which is available from the"
            " Stationery Office. If you are still in doubt, contact the"
            " Classification Advisory Service on (01702) 366077."
        ),
    )

    # Temporary Exported Goods fields (teg_ prefix)
    teg_origin_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="Country Of Origin",
        help_text=(
            "Select the country, or group of countries (e.g. Any EU Country)"
            " that the temporary exported goods originate from."
        ),
    )

    teg_total_quantity = models.DecimalField(
        null=True,
        max_digits=9,
        decimal_places=2,
        verbose_name="Total Quantity",
        validators=[at_least_0],
    )

    teg_total_value = models.DecimalField(
        null=True,
        max_digits=9,
        decimal_places=2,
        verbose_name="Total Value (Euro)",
        validators=[at_least_0],
    )

    teg_goods_description = models.CharField(
        null=True, max_length=4096, verbose_name="Goods Description"
    )

    teg_commodities = models.ManyToManyField(
        Commodity,
        related_name="+",
        verbose_name="Commodity Code",
        help_text=(
            "It is the responsibility of the applicant to ensure that the"
            " commodity code in this box is correct. If you are unsure of the"
            " correct commodity code, consult the HM Revenue and Customs"
            " Integrated Tariff Book, Volume 2, which is available from the"
            " Stationery Office. If you are still in doubt, contact the"
            " Classification Advisory Service on (01702) 366077."
        ),
    )

    # further questions (fq_ prefix)
    fq_similar_to_own_factory = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name=(
            "Do you manufacture goods which are similar to and at the same stage of"
            " processing in your own factory within the EU as the products to be"
            " re-imported? (Article 2 (2) (a) of Regulation (EC) No. 3036/94)"
        ),
        help_text=_ONCE_PER_YEAR,
    )

    fq_manufacturing_within_eu = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name=(
            "Are the main manufacturing processes of the similar goods performed in"
            " your own factory within the EU (i.e. sewing and assembly or knitting in"
            " the case of fully-fashioned garments obtained from yarn)? (Article 2 (2)"
            " (a) of Regulation (EC) No. 3036/94)"
        ),
        help_text=_ONCE_PER_YEAR,
    )

    fq_maintained_in_eu = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name=(
            "Have you maintained your textile manufacturing activity in the EU with"
            " respect to the nature of the products and their quantities? (Article 3 (3)"
            " of Regulation (EC) No. 3036/94)"
        ),
        help_text=_ONCE_PER_YEAR,
    )

    # if above is "No" this must be filled
    fq_maintained_in_eu_reasons = models.CharField(
        max_length=4000,
        blank=True,
        null=True,
        verbose_name="If not, please indicate reasons for the above or make reference to past correspondence.",
    )

    fq_employment_decreased = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Has your level of employment decreased? (Article 5 (4) of Regulation (EC) No. 3036/94)",
        help_text=_ONCE_PER_YEAR,
    )

    # if above is "Yes" this must be filled
    fq_employment_decreased_reasons = models.CharField(
        max_length=4000,
        blank=True,
        null=True,
        verbose_name="If so, please indicate reasons and attach statistics below if necessary, or make reference to past correspondence.",
    )

    fq_prior_authorisation = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        verbose_name=(
            "Have you applied for a prior authorisation in another Member State"
            " for the same quota period? (Article 3(4) or (5) of Regulation (EC) No. 3036/94)"
        ),
    )

    # if above is "Yes" this must be filled
    fq_prior_authorisation_reasons = models.CharField(
        max_length=4000,
        blank=True,
        null=True,
        verbose_name="If so, please attach a copy of your authorisation below, or make reference to past correspondence.",
    )

    fq_past_beneficiary = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        verbose_name=(
            "Are you applying as a past beneficiary with regard to the category and"
            " country concerned? (Article 3(4) of Regulation (EC) No. 3036/94)"
        ),
    )

    # if above is "Yes" this must be filled
    fq_past_beneficiary_reasons = models.CharField(
        max_length=4000,
        blank=True,
        null=True,
        verbose_name="If so, please attach justification below, or make reference to past correspondence.",
    )

    fq_new_application = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        verbose_name=(
            "Is this a new application with regard to the category and country"
            " concerned? (Article 3(5) (2) and (3) of Regulation (EC) No. 3036/94)"
        ),
    )

    # if above is "Yes" this must be filled
    fq_new_application_reasons = models.CharField(
        max_length=4000,
        blank=True,
        null=True,
        verbose_name=(
            "If so, please make reference to past correspondence, or attach justification"
            " below, that the value of the third country processing will not exceed"
            " 50% of the value of your Community production in the previous year."
        ),
    )

    fq_further_authorisation = models.CharField(
        max_length=3,
        choices=YesNoChoices.choices,
        null=True,
        verbose_name=(
            "Are you applying for a further authorisation with regard to the category"
            " and country concerned? (Article 3(5) (4) of Regulation (EC) No. 3036/94)"
        ),
    )

    # if above is "Yes" this must be filled
    fq_further_authorisation_reasons = models.CharField(
        max_length=4000,
        blank=True,
        null=True,
        verbose_name=(
            "If so, please attach evidence below, or make reference to past"
            " correspondence, that 50% of your previous authorisation has been"
            " re-imported or that 80% has been exported."
        ),
    )

    fq_subcontract_production = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name=(
            "Does the value of your Community production in the previous year include"
            " subcontract production? (If so and you have not yet given this"
            " information, please attach declarations from subcontractors that they will"
            " not apply for the same quantities) (Article 2(2)(a) of Regulation (EC) No."
            " 3036/94)"
        ),
        help_text=_ONCE_PER_YEAR,
    )

    documents = models.ManyToManyField(OutwardProcessingTradeFile, related_name="+")


class OPTChecklist(ChecklistBase):
    import_application = models.OneToOneField(
        OutwardProcessingTradeApplication, on_delete=models.PROTECT, related_name="checklist"
    )

    # This base class field is not needed.
    endorsements_listed = None

    operator_requests_submitted = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Operator requests submitted to commission by set deadline?",
    )

    authority_to_issue = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Authority to issue confirmed by European Commission?",
    )
