from datetime import datetime

import pytz
from django.conf import settings

from web.models import CFSScheduleParagraph, CountryTranslationSet, Template


def add_cfs_schedule_data():
    t = Template.objects.create(
        template_name="CFS Schedule template",
        template_type="CFS_SCHEDULE",
        application_domain="CA",
    )

    CFSScheduleParagraph.objects.bulk_create(
        [
            CFSScheduleParagraph(
                template=t,
                order=1,
                name="SCHEDULE_HEADER",
                content="Schedule to Certificate of Free Sale",
            ),
            CFSScheduleParagraph(
                template=t,
                order=2,
                name="SCHEDULE_INTRODUCTION",
                content="[[EXPORTER_NAME]], of [[EXPORTER_ADDRESS_FLAT]] has made the following legal declaration in relation to the products listed in this schedule:",
            ),
            CFSScheduleParagraph(
                template=t, order=3, name="IS_MANUFACTURER", content="I am the manufacturer."
            ),
            CFSScheduleParagraph(
                template=t,
                order=4,
                name="IS_NOT_MANUFACTURER",
                content="I am not the manufacturer.",
            ),
            CFSScheduleParagraph(
                template=t,
                order=5,
                name="EU_COSMETICS_RESPONSIBLE_PERSON",
                content="I am the responsible person as defined by the EU Cosmetics Regulation 1223/2009 and I am the person responsible for ensuring that the products listed in this schedule meet the safety requirements set out in the EU Cosmetics Regulation 1223/2009",
            ),
            CFSScheduleParagraph(
                template=t,
                order=6,
                name="LEGISLATION_STATEMENT",
                content="I certify that these products meet the safety requirements set out under UK and EU legislation, specifically:",
            ),
            CFSScheduleParagraph(
                template=t,
                order=7,
                name="ELIGIBILITY_ON_SALE",
                content="These products are currently sold on the EU market.",
            ),
            CFSScheduleParagraph(
                template=t,
                order=8,
                name="ELIGIBILITY_MAY_BE_SOLD",
                content="These products meet the product safety requirements to be sold on the EU market.",
            ),
            CFSScheduleParagraph(
                template=t,
                order=9,
                name="GOOD_MANUFACTURING_PRACTICE",
                content="These products are manufactured in accordance with the Good Manufacturing Practice standards set out in UK and EU law",
            ),
            CFSScheduleParagraph(
                template=t,
                order=10,
                name="COUNTRY_OF_MAN_STATEMENT",
                content="The products were manufactured in [[COUNTRY_OF_MANUFACTURE]]",
            ),
            CFSScheduleParagraph(
                template=t,
                order=11,
                name="COUNTRY_OF_MAN_STATEMENT_WITH_NAME",
                content="The products were manufactured in [[COUNTRY_OF_MANUFACTURE]] by [[MANUFACTURED_AT_NAME]]",
            ),
            CFSScheduleParagraph(
                template=t,
                order=12,
                name="COUNTRY_OF_MAN_STATEMENT_WITH_NAME_AND_ADDRESS",
                content="The products were manufactured in [[COUNTRY_OF_MANUFACTURE]] by [[MANUFACTURED_AT_NAME]] at [[MANUFACTURED_AT_ADDRESS_FLAT]]",
            ),
            CFSScheduleParagraph(template=t, order=13, name="PRODUCTS", content="Products"),
        ]
    )


DATETIME_FORMAT = "%d-%b-%Y %H:%M:%S"


def remove_templates():
    Template.objects.all().delete()


def add_cfs_declaration_templates():
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("01-MAY-2015 16:23:30", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Spanish",
        template_type="CFS_DECLARATION_TRANSLATION",
        application_domain="CA",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("05-MAR-2019 12:27:57", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="French",
        template_type="CFS_DECLARATION_TRANSLATION",
        application_domain="CA",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("24-APR-2015 08:59:21", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Portuguese",
        template_type="CFS_DECLARATION_TRANSLATION",
        application_domain="CA",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("23-APR-2015 16:25:35", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Russian",
        template_type="CFS_DECLARATION_TRANSLATION",
        application_domain="CA",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("24-APR-2015 09:01:34", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Turkish",
        template_type="CFS_DECLARATION_TRANSLATION",
        application_domain="CA",
    )


def add_schedule_translation_templates():
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("13-FEB-2019 18:56:17", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Spanish CFS Schedule",
        template_code="CFS_SCHEDULE_TRANSLATION",
        template_type="CFS_SCHEDULE_TRANSLATION",
        application_domain="CA",
        country_translation_set=CountryTranslationSet.objects.get(name="Spanish"),
    )


def add_declaration_templates():
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("13-APR-2018 16:40:06", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="General Declaration of Truth",
        template_code="IMA_GEN_DECLARATION",
        template_type="DECLARATION",
        application_domain="IMA",
        template_title="Declaration of Truth",
        template_content="I am the applicant for this licence or I am authorised to act on their behalf. I undertake that if a licence is granted it will be used solely to import goods which are the property of the applicant or lawfully in the custody of the applicant. I confirm that I am legally entitled to be in possession of any export licence presented with this application. I undertake to provide any information or documentation required by DIT in connection with this application or in connection with any transaction arising from the use of any licence granted in response to this application. I am aware that DIT may use information in this application for its administration of import policy and that the information may be passed for similar purposes to the Commission of the European Union and HM Revenue & Customs. I, the undersigned, certify that the information provided in this application is true and given in good faith and that I am established in the European Union.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("26-APR-2013 13:25:31", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="OPT Declaration",
        template_code="IMA_OPT_DECLARATION",
        template_type="DECLARATION",
        application_domain="IMA",
        template_title="Declaration of Truth",
        template_content="""I hereby declare that the particulars contained in this application are accurate and the documents attached are authentic and I submit the following documents:

1.  contracts,

2.  proof of origin of the goods temporarily exported, and

3.  other documents to support this application (numbered).

I also undertake:

I.  to present at the request of the competent authorities any supplementary documentation or information they consider necessary to issue the prior authorisation and to accept, if need be, the control by the competent authorities of the stock records relating to the authorisation;

II.  to retain such stock records for a period of three years from the end of the calendar year to the issue of the authorisation(s);

III.  to make clearly identifiable the goods temporarily exported and re-imported;

IV.  to make available all other evidence or samples the competent authorities deem necessary to control the use of this authorisation; and

V.  to return the prior authorisation at the latest within 15 days of the expiry period.

I request the issue of a prior authorisation for the goods detailed in the application""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("26-APR-2013 13:25:31", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Wood Affidavit",
        template_code="IMA_WD_DECLARATION",
        template_type="DECLARATION",
        application_domain="IMA",
        template_title="Affidavit",
        template_content="""I, the undersigned, do hereby make the following declarations:
As regards my application for a quota authorisation, I commit to:
(1) assign the products concerned to the prescribed processing within one year from the date on which the customs declaration for release for free circulation, containing the exact description of the goods and the TARIC codes, was accepted by the competent customs authorities;
(2) keep adequate records in the Member State where the authorisation was granted enabling the Licence Office to carry out any checks which they consider necessary to ensure that the products are actually assigned to the prescribed processing, and to retain such records;
(3) enable the Licence Office to trace the products concerned to their satisfaction in the premises of the undertaking concerned throughout their processing;
(4) notify the Licence Office of all factors which may affect the authorisation.
I, the undersigned, do hereby solemnly verify contents of my above affidavit are true and correct to my knowledge and no part of it is false.""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("19-APR-2018 13:18:14", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Prior Surveillance Declaration",
        template_code="IMA_SPS_DECLARATION",
        template_type="DECLARATION",
        application_domain="IMA",
        template_title="Declaration of Truth",
        template_content="I am the applicant for this licence or I am authorised to act on their behalf. I undertake that if a licence is granted it will be used solely to import goods which are the property of the applicant. I confirm that I am legally entitled to be in possession of any export licence presented with this application. I undertake to provide any information or documentation required by DIT in connection with this application or in connection with any transaction arising from the use of any licence granted in response to this application. I am aware that DIT may use information in this application for its administration of import policy and that the information may be passed for similar purposes to the Commission of the European Communities and HM Revenue ; Customs. I, the undersigned, certify that the information provided in this application is true and given in good faith.",
    )


def add_endorsement_templates():
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-JAN-2023 13:00:00", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Test Endorsement 1",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Test Endorsement Number 1",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-JAN-2023 13:00:00", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Test Endorsement 2",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Test Endorsement Number 2",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-FEB-2019 13:04:04", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 1 (must be updated each year)",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid only for goods loaded onto the exporting means of transport, in the country of origin, on or before 31 December 2016",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("24-APR-2014 13:26:05", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 10",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_title="Surveillance",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:34:26", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 11",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_title="Free Circulation:  Valid only for goods accompanied by a valid T2 document or a document having equivalent effect",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:08:18", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 13",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_title="Valid only for goods for re-export outside the EC.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("17-SEP-2018 11:33:41", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Open Individual Licence endorsement",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="""OPEN INDIVIDUAL LICENCE Not valid for goods originating in or consigned from Iran, North Korea, Libya, Syria or the Russian Federation.(including any previous name by which these territories have been known).
This licence is only valid if the firearm and its essential component parts (Barrel, frame, receiver (including both upper or lower receiver), slide, cylinder, bolt or breech block) are marked with name of manufacturer or brand, country or place of manufacturer, serial number, year of manufacture and model (if an essential component is too small to be fully marked it must at least be marked with a serial number or alpha-numeric or digital code).""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:56:07", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 15",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Surveillance.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:57:30", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 16",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Not valid for goods entered to Inward Processing Relief.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:36:26", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 17",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid only for use on or after 1 July 1994",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:37:38", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 19",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid only for use on or after 1 June 2001",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-FEB-2019 13:04:13", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 2 (must be updated each year)",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid only for use on or after 1 January 2016",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:38:24", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 20",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid only for fabrics woven on looms solely by hand or foot; for articles made from such fabrics and sewn exclusively by hand or for traditional folklore products made by hand as the case may be.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:38:35", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 21",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Folkloric: Valid only for traditional folklore products, made by hand",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:38:45", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 22",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Batik : Valid only for traditional batik fabrics and articles made from such fabrics whether sewn by hand or on a sewing machine operated by hand or foot",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:12:18", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 25",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Value, C.i.f., in euro  ,   ,    on licence application (Unit Price	  .   euro per tonne)",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:47:32", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 28",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid for goods shipped on or before 28 October 2004",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:05:48", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Replacement licence ensorsement",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="This licence is issued in replacement of Import Licence No. <NUMBER>",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:07:16", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Replacement for revoked licence endorsement",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="This licence is issued in replacement of the following licence, which has been revoked:- Import Licence No.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:01:25", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 32",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid only for goods of a quality lower than prime",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:06:30", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 34",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="This licence is a renewal of the following Import Licence no: <NUMBER>",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:00:18", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 35",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Surveillance : This surveillance document has a tolerance of 5% on the quantity indicated in box 11.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:03:08", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 4",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Rate of Exchange to be applied is 1 Pound Sterling = (1/ECU RATE) euro. Therefore, the Pounds Sterling value of this licence is (ECU RATE * VALUE OF LICENCE)",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("08-SEP-2016 15:53:50", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Firearms EU Transfer within Directive 91/477/EEC",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Your attention is drawn to the further conditions listed on the Schedule attached to this licence.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:32:57", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 45",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="This import licence is not valid for goods originating in or consigned from Serbia or Montenegro.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:32:46", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 46",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="This licence is not valid for the importation of goods which originate in, are consigned from, or have been transited through the areas of Bosnia-Herzegovina under the control of the Bosnian",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:32:32", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 47",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Serb forces.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:02:46", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 48",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="A further condition of this licence is that it must be returned to this Branch within 15 days of expiry if it is unused/partially unused",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:32:14", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 49",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="* and with technical features such as hermetic pads containing gas or fluid, mechanical components which absorb or neutralise impact or materials such as low-density polymers.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-FEB-2019 13:04:17", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 5",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="This licence is equivalent to (QUANTITY) (UNITS)",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:03:42", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 50",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="A further condition of this licence is that it must be returned to this Branch within 10 working days of expiry.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:31:33", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 6",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid only for goods loaded onto the exporting means of transport, in the country of origin, on or before 6 January 2000",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:31:15", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 61",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid only for goods loaded onto the exporting means of transport, in the country of origin, on or after 1 January 2005",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:59:33", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 62",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Value, CIF, in Euro",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:30:47", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 7",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="A further condition of the issue of this import licence is that it may not be loaned or transferred, whether for a consideration or free of charge, by the person in whose name the document was issued.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:30:23", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 71",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid only for goods shipped from China between 11 June 2005 and 19 July 2005 inclusive",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:30:10", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 72",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Valid only for goods shipped from China before 11 June 2005",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:02:05", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 73",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="It is an offence to be in breach of your authority issued under the Firearms Act 1968, as amended, limiting the number of prohibited weapons & ammunition which you may possess at any one time.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 10:01:50", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 8",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="EXCEPTIONAL LICENCE",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("29-APR-2013 09:29:31", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Endorsement 9",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Short shipment: Quantity applied for has been reduced",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("09-AUG-2019 15:14:26", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Firearms Sanctions COO (AC or AY)",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Not valid for items originating in Iran, North Korea, Libya, Syria or the Russian Federation.(including any previous name by which these territories have been known).",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("09-AUG-2019 15:13:54", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Firearms Sanctions COC (AY)",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Not valid for items consigned from Iran, North Korea, Libya, Syria or the Russian Federation.(including any previous name by which these territories have been known).",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("09-AUG-2019 15:14:09", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Firearms Sanctions COO & COC (AC & AY)",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria or the Russian Federation.(including any previous name by which these territories have been known).",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("07-MAY-2015 15:40:18", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Proof House",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="This licence is issued subject to the following conditions: It is not valid for goods originating in or consigned from Iran, North Korea, Libya, Syria or the Russian Federation. No person can use the licence without the permission of the Proof Master; the Proof House must record any permissions that it has granted; the Proof House must record details of every importation made against licence upon its arrival at the Proof House; and the Proof House must permit the proper officer of HM Revenue and Customs to inspect any records relating to importations made using the licence.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("19-FEB-2019 15:04:20", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Anti personnel mines (NO DEAL)",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="""The licence has been issued because you hold authority of the Secretary of State for Defence under Section 4 of the Landmines Act 1988 to possess. You are reminded of the conditions set out in that authority. You also have a responsibility to comply with any legislation relating to explosives, if relevant, and that this import licence does not replace this responsibility. Please contact the Health and Safety Executive for further advice.
The movement of landmines from the port to their final destination is covered by the provisions of the Landmines Act 1998 and must be carried out by suitably authorised persons.
The Ministry of Defence requested that you include details of your UK mine holdings in due course.""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("03-MAY-2016 15:53:27", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Steel Prior Surveillance",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="This surveillance document remains valid as long as the unit price remains within 5% of the listed unit price.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("05-MAR-2019 12:25:24", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Russian Sanctions",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="This licence has been issued for imports from the Russian Federation where the appplicant has proven that the goods meet the terms of the derogation specified in Article 2 of EU Council Decision 2014/512/CFSP, covering goods subject to a contract concluded and paid for before 1 August 2014.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("19-DEC-2014 08:23:55", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Royal Gibraltar Police",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="It is a condition of this import licence that the goods be transferred upon arrival in the UK, in the presence of an officer of Sussex Police, to an authorised representative of LGC Laboratories Ltd. The authorised representative will be responsible for the security of the goods from the point of their importation until their exportation to Gibraltar.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("05-JAN-2016 08:30:16", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Section 5 Carrier",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="This licence is only valid when the goods are imported using a carrier authorised to carry Section 5 goods.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("05-JAN-2016 09:53:22", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Section 5 carrier & EU transfer temporary endorsement",
        template_type="ENDORSEMENT",
        application_domain="IMA",
        template_content="""This licence is only valid for section 5 goods when they are imported using a carrier authorised to carry Section 5 goods.
EU transfers falling within the provisions of Directives 91/477/EEC and 93/15/EEC must have a transfer licence issued by the sending Member State.""",
    )


def add_email_templates():
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-FEB-2019 12:50:10", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Stop Case Email",
        template_code="STOP_CASE",
        template_type="EMAIL_TEMPLATE",
        application_domain="IMA",
        template_title="ICMS Case Reference [[CASE_REFERENCE]] Stopped",
        template_content="Processing on ICMS Case Reference [[CASE_REFERENCE]] has been stopped. Please contact ILB if you believe this is in error or require further information.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("19-MAR-2019 11:01:12", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Further Information Request email",
        template_code="IMA_RFI",
        template_type="EMAIL_TEMPLATE",
        application_domain="IMA",
        template_title="[[CASE_REFERENCE]] Further Information Request",
        template_content=f"""Dear [[IMPORTER_NAME]],

To enable ILB to process your application, I am writing to ask you for [FURTHER INFORMATION / CLARIFICATION] regarding [DESCRIBE WHAT FURTHER INFORMATION IS NEEDED / WHAT IS UNCLEAR, MAKE SUGGESTIONS IF RELEVANT]

You must respond to this information request via the information request  link now assigned to the case. Your application will not be processed further until you respond to this request.

The application will be closed if the requested response is not received within 5 working days of our receipt of the original application.

Please do not hesitate to contact { settings.ILB_CONTACT_EMAIL } if you have any queries regarding your application.  Please quote the following reference number in any correspondence: [[CASE_REFERENCE]].

Yours sincerely,

[[CASE_OFFICER_NAME]]""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("19-MAR-2019 11:00:27", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Application Update email",
        template_code="IMA_APP_UPDATE",
        template_type="EMAIL_TEMPLATE",
        application_domain="IMA",
        template_title="[[CASE_REFERENCE]] Request for Application Update",
        template_content=f"""Dear [[IMPORTER_NAME]]

To enable ILB to process your application, I am writing to ask you for application updates regarding [DESCRIBE WHAT UPDATES ARE NEEDED / WHAT IS UNCLEAR, MAKE SUGGESTIONS IF RELEVANT]

You must make the requested amendments via the update  link now assigned to the case. Your application will not be processed further until you submit the updates.

The application will be closed if the requested updates are not received within 5 working days of our receipt of the original application.

Please do not hesitate to contact { settings.ILB_GSI_CONTACT_EMAIL } if you have any queries regarding your application.  Please quote the following reference number in any correspondence: [[CASE_REFERENCE]].

This application will be closed if all requested updates are not completed within 5 working days of our receipt of the original application.

Yours sincerely,

[[CASE_OFFICER_NAME]]""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-FEB-2019 12:49:28", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Licence Revocation email",
        template_code="LICENCE_REVOKE",
        template_type="EMAIL_TEMPLATE",
        application_domain="IMA",
        template_title="ICMS Licence [[LICENCE_NUMBER]] Revoked",
        template_content="Licence [[LICENCE_NUMBER]] has been revoked. Please contact ILB if you believe this is in error or require further information.",
    )
    # TODO: template extracted from the test system not from the db as missing
    # search IMA_SANCTION_EMAIL to see usage
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-FEB-2019 11:06:59", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Sanction email",
        template_code="IMA_SANCTION_EMAIL",
        template_type="EMAIL_TEMPLATE",
        application_domain="IMA",
        template_title="Import Sanctions and Adhoc Licence",
        template_content="""
Dear Colleagues

We have received an import licence application from:
[[IMPORTER_NAME]]
[[IMPORTER_ADDRESS]]

The application is for the following:

[[GOODS_DESCRIPTION]]

Thanks and best regards

[[CASE_OFFICER_NAME]]
[[CASE_OFFICER_EMAIL]]
[[CASE_OFFICER_PHONE]]
""",
    )

    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-FEB-2019 11:06:59", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Firearms Constabulary email",
        template_code="IMA_CONSTAB_EMAIL",
        template_type="EMAIL_TEMPLATE",
        application_domain="IMA",
        template_title="Import Licence RFD Enquiry",
        template_content="""Dear Colleagues

[[CASE_REFERENCE]]

We have received an import licence application from:

[[IMPORTER_NAME]]
[[IMPORTER_ADDRESS]]

The application is for:
[[GOODS_DESCRIPTION]]

Grateful if the Police can advise on the validity of the RFD/Firearms/Shotgun Certificate, and whether there are any objections to the issuing of the import licence.
Grateful if the Police can validate the RFD / and Section 1 and 2 authority/authorities on the applicants ICMS account. (delete as appropriate).
Grateful if Home Office can confirm use of obsolete calibre or any other Section 58(2) exemption and if there are any reasons why an import licence should not be issued. (delete if not applicable)
Grateful if the Home Office can validate the Section 5 authority on the applicants ICMS account. (delete if not Section 5)
Grateful if you can check the attached deactivation certificate and advise as to whether or not it is valid and matches your records. (DELETE IF NOT DEACTIVATED)

Please note that the import licence will not be issued until we have had your response/responses to this e-mail.

Thanks and best regards

[[CASE_OFFICER_NAME]]
[[CASE_OFFICER_EMAIL]]
[[CASE_OFFICER_PHONE]]""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-FEB-2019 12:31:29", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Case reopening email",
        template_code="CASE_REOPEN",
        template_type="EMAIL_TEMPLATE",
        application_domain="IMA",
        template_title="Case Reopened: [[CASE_REFERENCE]]",
        template_content="ILB has reopened case reference [[CASE_REFERENCE]] and will resume processing on this case. Please contact ILB for further information.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("05-DEC-2013 17:20:07", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Publish Mailshot Email",
        template_code="PUBLISH_MAILSHOT",
        template_type="EMAIL_TEMPLATE",
        application_domain="IMA",
        template_title="New Mailshot",
        template_content="A new mailshot has been published and is available to view from your workbasket.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("05-DEC-2013 17:20:07", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Retract Mailshot Email",
        template_code="RETRACT_MAILSHOT",
        template_type="EMAIL_TEMPLATE",
        application_domain="IMA",
        template_title="Retracted Mailshot",
        template_content="A published mailshot has been retracted.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-FEB-2019 12:32:26", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Certificate Revocation email",
        template_code="CERTIFICATE_REVOKE",
        template_type="EMAIL_TEMPLATE",
        application_domain="CA",
        template_title="ICMS Certificate(s) Revoked",
        template_content="Certificate(s) [[CERTIFICATE_REFERENCES]] have been revoked. Please contact ILB if you believe this is in error or require further information.",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("19-MAR-2019 11:01:26", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Further Information Request Email",
        template_code="IAR_RFI_EMAIL",
        template_type="EMAIL_TEMPLATE",
        application_domain="IAR",
        template_title="[[REQUEST_REFERENCE]] Further Information Request",
        template_content=f"""Dear [[REQUESTER_NAME]],

To enable ILB to process your application, I am writing to ask you for [FURTHER INFORMATION / CLARIFICATION] regarding [DESCRIBE WHAT FURTHER INFORMATION IS NEEDED / WHAT IS UNCLEAR, MAKE SUGGESTIONS IF RELEVANT]

You must only reply via the information request link now assigned to the request available when you log in.

Please do not hesitate to contact { settings.ILB_GSI_CONTACT_EMAIL } if you have any queries regarding your application. Please quote the following reference number in any correspondence: [[REQUEST_REFERENCE]].

Yours sincerely,

[[CURRENT_USER_NAME]]""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-AUG-2018 15:47:36", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="HSE Enquiry Email",
        template_code="CA_HSE_EMAIL",
        template_type="EMAIL_TEMPLATE",
        application_domain="CA",
        template_title="Biocidal Product Enquiry",
        template_content="""Dear Colleagues

[[CASE_REFERENCE]]

We have received a [[APPLICATION_TYPE]] application from:
[[EXPORTER_NAME]]
[[EXPORTER_ADDRESS]]
[[CONTACT_EMAIL]]

The application is for the following countries:
[[CERT_COUNTRIES]]

The application is for the following biocidal products:
[[SELECTED_PRODUCTS]]

Grateful for your guidance on the items listed.

Thanks and best regards

[[CASE_OFFICER_NAME]]
[[CASE_OFFICER_EMAIL]]
[[CASE_OFFICER_PHONE]]""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("22-AUG-2018 15:47:36", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="BEIS OPSS Enquiry Email",
        template_code="CA_BEIS_EMAIL",
        template_type="EMAIL_TEMPLATE",
        application_domain="CA",
        template_title="Good Manufacturing Practice Application Enquiry",
        template_content="""Dear Colleagues

[[CASE_REFERENCE]]

We have received a [[APPLICATION_TYPE]] application from:
[[EXPORTER_NAME]]
[[EXPORTER_ADDRESS]]

Please review and advise whether or not this branch can issue a GMP Certificate for this
request.

MANUFACTURER:
[[MANUFACTURER_NAME]]
[[MANUFACTURER_ADDRESS]]
[[MANUFACTURER_POSTCODE]]

RESPONSIBLE PERSON:
[[RESPONSIBLE_PERSON_NAME]]
[[RESPONSIBLE_PERSON_ADDRESS]]
[[RESPONSIBLE_PERSON_POSTCODE]]

NAME OF BRANDS:
[[BRAND_NAMES]]

Thanks and best regards

[[CASE_OFFICER_NAME]]
[[CASE_OFFICER_EMAIL]]
[[CASE_OFFICER_PHONE]]""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("19-MAR-2019 11:00:11", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Application Update Email",
        template_code="CA_APPLICATION_UPDATE_EMAIL",
        template_type="EMAIL_TEMPLATE",
        application_domain="CA",
        template_title="[[CASE_REFERENCE]] Request for Application Update",
        template_content=f"""Dear [[EXPORTER_NAME]]

To enable ILB to process your application, I am writing to ask you for application updates regarding [DESCRIBE WHAT UPDATES ARE NEEDED / WHAT IS UNCLEAR, MAKE SUGGESTIONS IF RELEVANT].

You must select the responsible person statement if you have placed the product on the EU market.  This only applies to cosmetics. [DELETE IF NOT APPLICABLE]

You must make the requested amendments via the update  link now assigned to the case. The application will not be processed further until you submit the updates.

The application will be closed if the requested updates are not received within 5 working days of our receipt of the original application.

Please do not hesitate to contact { settings.ILB_GSI_CONTACT_EMAIL } if you have any queries regarding your application. Please quote the following reference number in any correspondence: [[CASE_REFERENCE]].

Yours sincerely,

[[CASE_OFFICER_NAME]]""",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("19-MAR-2019 11:01:42", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Further Information Request Email",
        template_code="CA_RFI_EMAIL",
        template_type="EMAIL_TEMPLATE",
        application_domain="CA",
        template_title="[[CASE_REFERENCE]] Further Information Request",
        template_content=f"""Dear [[EXPORTER_NAME]],

To enable ILB to process your application, I am writing to ask you for [FURTHER INFORMATION / CLARIFICATION] regarding [DESCRIBE WHAT FURTHER INFORMATION IS NEEDED / WHAT IS UNCLEAR, MAKE SUGGESTIONS IF RELEVANT].

You must respond to this information request via the information request link now assigned to the case. Your application will not be processed further until you respond to this request.

The application will be closed if the requested response is not received within 5 working days of our receipt of the original application.

Please do not hesitate to contact { settings.ILB_GSI_CONTACT_EMAIL } if you have any queries regarding your application. Please quote the following reference number in any correspondence: [[CASE_REFERENCE]].

Yours sincerely,

[[CASE_OFFICER_NAME]]""",
    )


def add_letter_templates():
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("17-DEC-2013 17:10:00", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Firearms Section 5 EC Schedule",
        template_code="SCHEDULE_FIREARMS_SEC5_EC",
        template_type="LETTER_TEMPLATE",
        application_domain="IMA",
        template_content='<p align="justify">Import licence no. [[LICENCE_NUMBER]] is not valid for firearms, ammunition and component parts transferred from the Community Area unless accompanied by a licence issued by the competent authority of the exporting Member State authorising the transfer of the firearms, ammunition and component parts to the UK or, in the case of a transfer by a firearms dealer who holds a valid open licence to transfer firearms, ammunition and component parts issued by the competent authorities in the Member State from which the firearms, ammunition and component parts are to be exported, a document relating to that open licence. The said transfer licence or document and this import licence must accompany the firearms, ammunition and component parts until they reach their destination in the UK.</p>',
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("05-JAN-2016 09:57:40", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Shipped from EU Member State to UK under Directive 91/477/EEC (Section 5)",
        template_code="COVER_FIREARMS_SEC5_EC",
        template_type="LETTER_TEMPLATE",
        application_domain="IMA",
        template_content='<p align="justify">Dear [[CONTACT_NAME]]</p><p align="justify"><b>Transfers to the UK from the European Community - Import licence no. [[LICENCE_NUMBER]]</b></p><p align="left">Your request for an import licence dated [[APPLICATION_SUBMITTED_DATE]], has been approved. Your import licence is attached. The expiry date of the import licence is [[LICENCE_END_DATE]]. and you may now transfer the Section 5 items listed on the import licence under EU Directive 91/477/EEC. The enclosed import licence is the UK prior consent under this Directive and should be presented to the competant authorities in the transferring Member State in order to obtain the transfer licence.</p><p align="left">Your import licence is not valid unless accompanied by a transfer licence which you must obtain from [[COUNTRY_OF_CONSIGNMENT]], before transferring the items listed to the UK. The transfer licence and enclosed import licence must accompany the items listed until they reach their destination in the UK. If you are unable to obtain a transfer licence issued by the transferring Member State you should contact this office for advice before making the transfer.</p><p align="left">It is a criminal offence to import Firearms into the UK which have not been proved in a C.I.P (the international proof governing body) approved Proof House, without giving written notification to the British Proof Authority within 7 days of their entry or submitting for proof within 28 days of their entry. It is also a criminal offence to export a firearm which is not marked with a valid Proof Mark. Exports of firearms and ammunition are subject to export controls. You will find detailed advice at https://www.gov.uk/beginners-guide-to-export-controls.</p><p align="justify">This licence is only valid for section 5 goods when they are imported using a carrier authorised to carry Section 5 goods.</p>',
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("17-SEP-2018 12:22:06", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Shipped from EU Member State to UK",
        template_code="COVER_FIREARMS_SEC5_EC_OUTSIDE_DIRECTIVE",
        template_type="LETTER_TEMPLATE",
        application_domain="IMA",
        template_content='<p align="justify">Dear [[CONTACT_NAME]]</p><p align="justify"><b>Transfers to the UK from the European Community - Import licence no. [[LICENCE_NUMBER]]</b></p><p align="left">Your request for an import licence dated [[APPLICATION_SUBMITTED_DATE]], has been approved. Your import licence is attached. The expiry date of the import licence is [[LICENCE_END_DATE]]. and you may now transfer the items listed on the import licence to the UK.</p><p align="left">This licence is only valid if the firearm and its essential component parts (Barrel, frame, receiver (including both upper or lower receiver), slide, cylinder, bolt or breech block) are marked with name of manufacturer or brand, country or place of manufacture, serial number, year of manufacture and model (if an essential component is too small to be fully marked it must be marked with a serial number or alpha-numeric or digital code).</p><p align="left">This licence is only valid for section 5 goods when they are imported using a carrier authorised to carry Section 5 goods.</p><p align="justify">EU transfers falling within the provisions of Directives 91/477/EEC and 93/15/EEC must have a transfer licence issued by the sending Member State.</p>',
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("17-SEP-2018 12:23:15", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Shipped from outside the EU to UK",
        template_code="COVER_FIREARMS_SEC5_NOT_EU",
        template_type="LETTER_TEMPLATE",
        application_domain="IMA",
        template_content='<p align="justify">Dear [[CONTACT_NAME]]</p><p align="justify"><b>Import to the UK from Outside of the European Community Import licence no. [[LICENCE_NUMBER]].</b></p><p align="left">Your request for an import licence on [[APPLICATION_SUBMITTED_DATE]] has been approved and has been placed in HM Revenue &amp; Customs CHIEF system. You will need to use the data on the attached notification to use your licence on CHIEF. The import licence is valid until [[LICENCE_END_DATE]]. and allows you to import the goods listed in the import licence originating in [[COUNTRY_OF_ORIGIN]] and consigned from [[COUNTRY_OF_CONSIGNMENT]], into the UK.</p><p align="left">In respect of Section 5 items, the authority given to you under Section 5 of the Firearms Act 1968, as amended, limits the number of Section 5 weapons, ammunition and component parts which you may hold at any one time. It is an offence to be in breach of a condition of this authority.</p><p align="left">This licence is only valid if the firearm and its essential component parts (Barrel, frame, receiver (including both upper or lower receiver), slide, cylinder, bolt or breech block) are marked with name of manufacturer or brand, country or place of manufacture, serial number, year of manufacture and model (if an essential component is too small to be fully marked it must be marked with a serial number or alpha-numeric or digital code).</p><p align="left">This licence is only valid for section 5 goods when they are imported using a carrier authorised to carry Section 5 goods.</p>',
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("05-JAN-2016 09:56:09", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Imported into Northern Ireland (Section 5)",
        template_code="COVER_FIREARMS_SEC5_N_IRELAND",
        template_type="LETTER_TEMPLATE",
        application_domain="IMA",
        template_content='<p align="justify">Dear [[CONTACT_NAME]]</p><p align="justify"><b>Import of firearms to Northern Ireland from Outside of the European Community Import licence no. [[LICENCE_NUMBER]].</b></p><p align="left">Your request for an import licence on [[APPLICATION_SUBMITTED_DATE]] has been approved and has been placed in HM Revenue &amp; Customs CHIEF system. You will need to use the data on the attached notification to use your licence on CHIEF. The import licence is valid until [[LICENCE_END_DATE]]. and allows you to import goods listed in the import licence, originating in [[COUNTRY_OF_ORIGIN]] and consigned from [[COUNTRY_OF_CONSIGNMENT]] into Northern Ireland.</p><p align="left">The authority given to you under Article 45 of the Firearms (Northern Ireland) Order 2004, limits the number of Article 6(1) weapons, ammunition and component parts which you may hold at any one time. It is an offence to be in breach of this authority.</p><p align="left">It is a criminal offence to import Firearms into the UK which have not been proved in a C.I.P (the international proof governing body) approved Proof House, without giving written notification to the British Proof Authority within 7 days of their entry or submitting for proof within 28 days of their entry. It is also a criminal offence to export a firearm which is not marked with a valid Proof Mark. Exports of firearms and ammunition are subject to export controls. You will find detailed advice at https://www.gov.uk/beginners-guide-to-export-controls.</p><p align="justify">This licence is only valid for section 5 goods when they are imported using a carrier authorised to carry Section 5 goods. </p><p align="justify">EU transfers falling within the provisions of Directives 91/477/EEC and 93/15/EEC must have a transfer licence issued by the sending Member State.</p>',
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("08-NOV-2019 10:30:57", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Firearms OIL Cover Letter",
        template_code="COVER_FIREARMS_OIL",
        template_type="LETTER_TEMPLATE",
        application_domain="IMA",
        template_content='<p align="justify">Dear [[CONTACT_NAME]]</p><p align="justify"><b>Import of firearms to the UK from outside of the European Community: </b><br/><b>Licence no. [[LICENCE_NUMBER]]</b></p><p align="left">Your request for an Open Individual Import Licence, on [[APPLICATION_SUBMITTED_DATE]], has been approved and has been electronically placed in HM Revenue &amp; Customs CHIEF system. You will need to use the data on the attached notification to use your licence on CHIEF.</p><p align="left">This approval is valid until [[LICENCE_END_DATE]]. and allows you to import firearms, component parts and/or ammunition, that fall to either Section 1 or Section 2 of the Firearms Act 1968 (as amended) originating in any country and consigned from any country into the UK.</p><p align="left">The ban on the import and possession of certain handguns (the Firearms (Amendment) Act 1997 and the Firearms (Amendment)(No 2) Act 1997) only applies to mainland Britain. It does not apply to Northern Ireland or the Isle of Man.</p><p align="left">This licence is only valid if the firearm and its essential component parts (Barrel, frame, receiver (including both upper or lower receiver), slide, cylinder, bolt or breech block) are marked with name of manufacturer or brand, country or place of manufacture, serial number, year of manufacture and model (if an essential component is too small to be fully marked it must be marked with a serial number or alpha-numeric or digital code).</p>',
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("14-APR-2015 12:09:48", DATETIME_FORMAT), is_dst=None
        ),
        is_active=False,
        template_name="Shipped from outside EU to UK (not Section 5)",
        template_code="COVER_FIREARMS_OUTSIDE_EU",
        template_type="LETTER_TEMPLATE",
        application_domain="IMA",
        template_content='<p align="justify">Dear [[CONTACT_NAME]]</p><p align="justify"><b>Import to the UK from Outside of the European Community - Import licence no. [[LICENCE_NUMBER]].</b></p><p align="left">Your request for an import licence on [[APPLICATION_SUBMITTED_DATE]] has been approved and has been placed in HM Revenue &amp; Customs CHIEF system. You will need to use the data on the attached notification to use your licence on CHIEF. The import licence is valid until [[LICENCE_END_DATE]]. and allows you to import the goods listed in the import licence originating in [[COUNTRY_OF_ORIGIN]] and consigned from [[COUNTRY_OF_CONSIGNMENT]], into the UK.</p><p align="left">It is a criminal offence to import Firearms into the UK which have not been proved in a C.I.P (the international proof governing body) approved Proof House, without giving written notification to the British Proof Authority within 7 days of their entry or submitting for proof within 28 days of their entry. It is also a criminal offence to export a firearm which is not marked with a valid Proof Mark. Exports of firearms and ammunition are subject to export controls. You will find detailed advice at https://www.gov.uk/beginners-guide-to-export-controls</p>',
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("05-JAN-2016 09:56:34", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Proof House",
        template_code="COVER_FIREARMS_PROOF_HOUSE",
        template_type="LETTER_TEMPLATE",
        application_domain="IMA",
        template_content='<p align="justify">Dear [[CONTACT_NAME]]</p><p align="justify"><b>The importation into the UK from outside the EU and the transfer from the EU to the UK of firearms, component parts thereof and ammunition - Import licence no. </b><b>[[LICENCE_NUMBER]]</b></p><p align="justify">Your request for an import licence dated [[APPLICATION_SUBMITTED_DATE]], has been approved. Your import licence is attached. The expiry date of the import licence is [[LICENCE_END_DATE]].</p><p align="justify">It is a criminal offence to import Firearms into the UK which have not been proved in a C.I.P (the international proof governing body) approved Proof House, without giving written notification to the British Proof Authority within 7 days of their entry or submitting for proof within 28 days of their entry. It is also a criminal offence to export a firearm which is not marked with a valid Proof Mark. Exports of firearms and ammunition are subject to export controls. You will find detailed advice at https://www.gov.uk/beginners-guide-to-export-controls.</p><p align="justify">This licence is only valid for section 5 goods when they are imported using a carrier authorised to carry Section 5 goods. </p><p align="justify">EU transfers falling within the provisions of Directives 91/477/EEC and 93/15/EEC must have a transfer licence issued by the sending Member State.</p>',
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("13-FEB-2014 13:40:13", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Anti-personnel Mines",
        template_code="COVER_FIREARMS_ANTI_PERSONNEL_MINES",
        template_type="LETTER_TEMPLATE",
        application_domain="IMA",
        template_content='<p align="justify">Dear [[CONTACT_NAME]]</p><p align="justify"><b>Importation of Inert Anti-personnel Mines - Import Licence Number: </b><b>[[LICENCE_NUMBER]]</b></p><p align="justify">Your request for an import licence dated [[APPLICATION_SUBMITTED_DATE]], has been approved. The import licence is valid until [[LICENCE_END_DATE]] and allows you to import the goods listed in the import licence originating in [[COUNTRY_OF_ORIGIN]] and consigned from [[COUNTRY_OF_CONSIGNMENT]], into the UK.</p><p align="justify">The licence has been issued because you hold authority of the Secretary of State for Defence under Section 4 of the Landmines Act 1988 to possess. You are reminded of the conditions set out in that authority.</p><p align="justify">You are also reminded that you have a responsibility to comply with any legislation relating to explosives, if relevant, and that this import licence does not replace this responsibility. If need be you should contact the Health and Safety Executive for further advice.</p><p align="justify">You are also reminded that the movement of the landmines from the port to their final destination is also covered by the provisions of the Landmines Act 1998 and must be carried out by suitably authorised persons.</p><p align="justify">The Ministry of Defence requested that you include details of your UK mine holdings in due course.</p>',
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("13-APR-2016 14:39:08", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Deactivated Firearms",
        template_code="COVER_FIREARMS_DEACTIVATED_FIREARMS",
        template_type="LETTER_TEMPLATE",
        application_domain="IMA",
        template_content='<p align="justify">Dear [[CONTACT_NAME]]</p><p align="justify"><b>Import into the UK from outside the EU or transfer from the EU to the UK of deactivated firearms - Import licence no. [[LICENCE_NUMBER]]</b></p><p align="justify">Your request for an import licence dated [[APPLICATION_SUBMITTED_DATE]], has been approved. Your import licence is attached. The expiry date of the import licence is [[LICENCE_END_DATE]].</p><p align="justify">Your import licence is invalid if the deactivated firearm being imported is not proof marked or does not meet the deactivation standards set out in Commission implementing Regulation 2015/2403 or any nationally set higher standard. It is a criminal offence to import or export a firearm not marked with a valid Proof Mark.</p>',
    )


def add_letter_fragment_templates():
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("18-JUL-2019 18:50:23", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Firearms Markings Standard",
        template_code="FIREARMS_MARKINGS_STANDARD",
        template_type="LETTER_FRAGMENT",
        application_domain="IMA",
    )
    Template.objects.get_or_create(
        start_datetime=pytz.timezone("UTC").localize(
            datetime.strptime("18-JUL-2019 18:50:23", DATETIME_FORMAT), is_dst=None
        ),
        is_active=True,
        template_name="Firearms Markings Non-Standard",
        template_code="FIREARMS_MARKINGS_NON_STANDARD",
        template_type="LETTER_FRAGMENT",
        application_domain="IMA",
    )
