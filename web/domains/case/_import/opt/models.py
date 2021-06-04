from django.db import models

from web.domains.file.models import File
from web.models.shared import YesNoNAChoices

from ..models import ImportApplication

_ONCE_PER_YEAR = """This question only needs to be completed once per year. If
you have already completed this question on a previous application this year,
you may select 'N/A'.""".replace(
    "\n", " "
)


class OutwardProcessingTradeApplication(ImportApplication):
    PROCESS_TYPE = "OutwardProcessingTradeApplication"

    customs_office_name = models.CharField(
        max_length=100, null=True, verbose_name="Requested customs supervising office name"
    )

    customs_office_address = models.TextField(
        max_length=4000, null=True, verbose_name="Requested customs supervising office address"
    )

    rate_of_yield = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, verbose_name="Rate of yield (kg per garment)"
    )

    rate_of_yield_calc_method = models.TextField(
        max_length=4000, blank=True, null=True, verbose_name="Rate of yield calculation method"
    )

    last_export_day = models.DateField(
        null=True, help_text="Requested last day of authorised exportation."
    )

    reimport_period = models.DecimalField(
        max_digits=9, decimal_places=2, null=True, verbose_name="Period for re-importation (months)"
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

    # TODO: ICMLST-594 add Compensating Products

    # TODO: ICMLST-596 add Temporary Exported Goods

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

    # TODO: add the rest of these "Further Questions"

    # Has your level of employment decreased?
    # (Article 5 (4) of Regulation (EC) No. 3036/94)
    # CHOICES: Yes,No,N/A
    # TOOLTIP: This question only needs to be completed once per year. If you
    # have already completed this question on a previous application this year,
    # you may select 'N/A'.
    #
    #   ^ if above is "Yes", this shows up (3-line textbox):
    #   Please indicate reasons and attach statistics below if necessary, or make reference to past correspondence.
    #
    #   also allows to upload files. either textbox must be filled in or file(s) uploaded ("You must enter this item, or attach statistics.")

    # Have you applied for a prior authorisation in another Member State for the
    # same quota period? (Article 3(4) or (5) of Regulation (EC) No. 3036/94)
    # CHOICES: Yes,No
    #
    #   ^ if above is "Yes", this shows up (3-line textbox):
    #   Please attach a copy of your authorisation below, or make reference to past correspondence.
    #
    #   also allows to upload files. either textbox must be filled in or file(s) uploaded  ("You must enter this item, or attach a copy.")

    # Are you applying as a past beneficiary with regard to the category and
    # country concerned? (Article 3(4) of Regulation (EC) No. 3036/94)
    # CHOICES: Yes,No
    #
    #   ^ if above is "Yes", this shows up (3-line textbox):
    #   Please attach justification below, or make reference to past correspondence.
    #
    #   also allows to upload files. either textbox must be filled in or file(s) uploaded  ("You must enter this item, or attach justification.")

    # Is this a new application with regard to the category and country
    # concerned? (Article 3(5) (2) and (3) of Regulation (EC) No. 3036/94)
    # CHOICES: Yes,No
    #
    #   ^ if above is "Yes", this shows up (3-line textbox):
    #   Please make reference to past correspondence, or attach justification
    #   below, that the value of the third country processing will not exceed
    #   50% of the value of your Community production in the previous year.
    #
    #   also allows to upload files. either textbox must be filled in or file(s) uploaded  ("You must enter this item, or attach justification.")

    # Are you applying for a further authorisation with regard to the category
    # and country concerned? (Article 3(5) (4) of Regulation (EC) No. 3036/94)
    # CHOICES: Yes,No
    #
    #   ^ if above is "Yes", this shows up (3-line textbox):
    #   If so please attach evidence below, or make reference to past
    #   correspondence, that 50% of your previous authorisation has been
    #   re-imported or that 80% has been exported.
    #
    #   also allows to upload files. either textbox must be filled in or file(s) uploaded  ("You must enter this item, or attach evidence.")

    # Does the value of your Community production in the previous year include
    # subcontract production? (If so and you have not yet given this
    # information, please attach declarations from subcontractors that they will
    # not apply for the same quantities) (Article 2(2)(a) of Regulation (EC) No.
    # 3036/94)
    # CHOICES: Yes,No,N/A
    # TOOLTIP: This question only needs to be completed once per year. If you
    # have already completed this question on a previous application this year,
    # you may select 'N/A'.
    #
    #   ^ if above is "Yes", file upload shows up which is mandatory ("Please ensure you have uploaded a declaration from the subcontractor.")

    supporting_documents = models.ManyToManyField(File, related_name="+")
