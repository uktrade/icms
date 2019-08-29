from django.db import models
from django.contrib.auth.models import (AbstractUser, Group)
from viewflow.models import Process
from .managers import AccessRequestQuerySet, ProcessQuerySet
from .mixins import Archivable, Sortable


class User(AbstractUser):

    # Statuses
    NEW = "NEW"
    BLOCKED = "BLOCKED"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    ACTIVE = "ACTIVE"
    STATUSES = ((NEW, 'NEW'), (BLOCKED, "Blocked"), (SUSPENDED, "Suspended"),
                (CANCELLED, "Cancelled"), (ACTIVE, 'ACTIVE'))

    # Password disposition
    TEMPORARY = 'TEMPORARY'
    FULL = 'FULL'
    PASSWORD_DISPOSITION = ((TEMPORARY, 'Temporary'), (FULL, 'Full'))

    title = models.CharField(max_length=20, blank=False, null=True)
    preferred_first_name = models.CharField(max_length=4000,
                                            blank=True,
                                            null=True)
    middle_initials = models.CharField(max_length=40, blank=True, null=True)
    organisation = models.CharField(max_length=4000, blank=False, null=True)
    department = models.CharField(max_length=4000, blank=False, null=True)
    job_title = models.CharField(max_length=320, blank=False, null=True)
    location_at_address = models.CharField(max_length=4000,
                                           blank=True,
                                           null=True)
    work_address = models.CharField(max_length=300, blank=False, null=True)
    date_of_birth = models.DateField(blank=False, null=True)
    security_question = models.CharField(max_length=4000,
                                         blank=False,
                                         null=True)
    security_answer = models.CharField(max_length=4000, blank=False, null=True)
    register_complete = models.BooleanField(blank=False,
                                            null=False,
                                            default=False)
    share_contact_details = models.BooleanField(blank=False,
                                                null=False,
                                                default=False)
    account_status = models.CharField(max_length=20,
                                      choices=STATUSES,
                                      blank=False,
                                      null=False,
                                      default=NEW)
    account_status_by = models.ForeignKey("self",
                                          on_delete=models.SET_NULL,
                                          blank=True,
                                          null=True,
                                          related_name='users_changed')
    account_status_date = models.DateField(blank=True, null=True)
    password_disposition = models.CharField(max_length=20,
                                            choices=PASSWORD_DISPOSITION,
                                            blank=True,
                                            null=True)

    class Display:
        display = [('title', 'first_name', 'last_name'),
                   ('organisation', 'email'), 'work_address']
        labels = ['Name', 'Job Details', 'Oragnisation Address']
        select = True


class Role(Group):
    group = models.OneToOneField(Group,
                                 on_delete=models.CASCADE,
                                 parent_link=True,
                                 related_name='roles')
    description = models.CharField(max_length=4000, blank=True, null=True)
    # Display order on the screen
    role_order = models.IntegerField(blank=False, null=False)

    def has_member(self, user):
        return user in self.user_set.all()

    @property
    def short_name(self):
        return self.name.split(':')[1]

    class Meta:
        ordering = ('role_order', )


class BaseTeam(models.Model):
    roles = models.ManyToManyField(Role)
    members = models.ManyToManyField(User)

    class Meta:
        abstract = True


class Team(BaseTeam):
    name = models.CharField(max_length=1000, blank=False, null=False)
    description = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        ordering = ('name', )

    class Display:
        display = ['name']
        labels = ['Name']
        edit = True


class Constabulary(Archivable, BaseTeam):
    EAST_MIDLANDS = 'EM'
    EASTERN = 'ER'
    ISLE_OF_MAN = 'IM'
    LONDON = 'LO'
    NORTH_EAST = 'NE'
    NORTH_WEST = 'NW'
    ROYAL_ULSTER = 'RU'
    SCOTLAND = 'SC'
    SOUTH_EAST = 'SE'
    SOUTH_WEST = 'SW'
    WEST_MIDLANDS = 'WM'

    REGIONS = ((EAST_MIDLANDS, 'East Midlands'), (EASTERN, 'Eastern'),
               (ISLE_OF_MAN, 'Isle of Man'), (
                   LONDON,
                   'London',
               ), (NORTH_EAST, 'North East'), (NORTH_WEST, 'North WEST'),
               (ROYAL_ULSTER, 'Royal Ulster'), (SCOTLAND, 'Scotland'),
               (SOUTH_EAST, 'South East'), (SOUTH_WEST, 'South West'),
               (WEST_MIDLANDS, 'West Midlands'))

    name = models.CharField(max_length=50, blank=False, null=False)
    region = models.CharField(max_length=3,
                              choices=REGIONS,
                              blank=False,
                              null=False)
    email = models.EmailField(max_length=254, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)

    @property
    def region_verbose(self):
        return dict(Constabulary.REGIONS)[self.region]

    class Display:
        display = ['name', 'region_verbose', 'email']
        labels = ['Constabulary Name', 'Constabulary Region', 'Email Address']
        edit = True
        archive = True


class PhoneNumber(models.Model):
    WORK = "WORK"
    FAX = "FAX"
    MOBILE = "MOBILE"
    HOME = "HOME"
    MINICOM = "MINICOM"
    TYPES = ((WORK, 'Work'), (FAX, 'Fax'), (MOBILE, 'Mobile'), (HOME, 'Home'),
             (MINICOM, 'Minicom'))
    phone = models.CharField(max_length=60, blank=False, null=False)
    type = models.CharField(max_length=30,
                            choices=TYPES,
                            blank=False,
                            null=False,
                            default=WORK)
    comment = models.CharField(max_length=4000, blank=True, null=True)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='phone_numbers')


class Email(models.Model):
    WORK = "WORK"
    HOME = "HOME"
    TYPES = ((WORK, 'Work'), (HOME, 'Home'))
    email = models.EmailField(max_length=254, blank=False, null=False)
    type = models.CharField(max_length=30,
                            choices=TYPES,
                            blank=False,
                            null=False,
                            default=WORK)
    portal_notifications = models.BooleanField(blank=False,
                                               null=False,
                                               default=False)
    comment = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        abstract = True


class AlternativeEmail(Email):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='alternative_emails')


class PersonalEmail(Email):
    is_primary = models.BooleanField(blank=False, null=False, default=False)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='personal_emails')


class OutboundEmail(models.Model):
    FAILED = 'FAILED'
    SENT = 'SENT'
    PENDING = 'PENDING'
    NOT_SENT = 'NOT_SENT'

    STATUSES = (
        (FAILED, 'Failed'),
        (SENT, 'Sent'),
        (PENDING, 'Pending'),
        (NOT_SENT, 'Not Sent'),
    )

    status = models.CharField(max_length=20,
                              choices=STATUSES,
                              blank=False,
                              null=False,
                              default=PENDING)
    last_requested_date = models.DateTimeField(auto_now_add=True,
                                               blank=False,
                                               null=False)
    format = models.CharField(max_length=20,
                              blank=False,
                              null=False,
                              default='Email')
    to_name = models.CharField(max_length=170, null=True)
    to_email = models.CharField(max_length=254, null=False)
    subject = models.CharField(max_length=4000, null=True)

    @property
    def attachments_count(self):
        return self.attachments.count()

    class Meta:
        ordering = ('-last_requested_date', )

    class Display:
        display = [
            'id', 'status', 'last_requested_date', 'format', 'to_email',
            'subject', 'attachments_count'
        ]
        labels = [
            'Mail Id', 'Status', 'Last Requested / Sent Date', 'Format',
            'To Email', 'Subject', 'Num. of Attachments'
        ]


class EmailAttachment(models.Model):
    mail = models.ForeignKey(OutboundEmail,
                             on_delete=models.CASCADE,
                             related_name='attachments')
    filename = models.CharField(max_length=200, blank=True, null=True)
    mimetype = models.CharField(max_length=200, null=False)
    text_attachment = models.TextField(null=True)


class Template(Archivable, models.Model):

    # Template types
    ENDORSEMENT = 'ENDORSEMENT'
    LETTER_TEMPLATE = 'LETTER_TEMPLATE'
    EMAIL_TEMPLATE = 'EMAIL_TEMPLATE'
    CFS_TRANSLATION = 'CFS_TRANSLATION'
    DECLARATION = 'DECLARATION'

    TYPES = (
        (ENDORSEMENT, 'Endorsement'),
        (LETTER_TEMPLATE, 'Letter template'),
        (EMAIL_TEMPLATE, 'Email template'),
        (CFS_TRANSLATION, 'CFS translation'),
        (DECLARATION, 'Declaration'),
    )

    # Application domain
    CERTIFICATE_APPLICATION = "CA"
    IMPORT_APPLICATION = "IMA"
    ACCESS_REQUEST = "IAR"

    DOMAINS = (
        (CERTIFICATE_APPLICATION, "Certificate Applications"),
        (IMPORT_APPLICATION, "Import Applications"),
        (ACCESS_REQUEST, "Access Requests"),
    )

    start_datetime = models.DateTimeField(blank=False, null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    template_name = models.CharField(max_length=100, blank=False, null=False)
    template_code = models.CharField(max_length=50, blank=True, null=True)
    template_type = models.CharField(max_length=20,
                                     choices=TYPES,
                                     blank=False,
                                     null=False)
    application_domain = models.CharField(max_length=20,
                                          choices=DOMAINS,
                                          blank=False,
                                          null=False)
    template_title = models.CharField(max_length=4000, blank=False, null=True)
    template_content = models.TextField(blank=False, null=True)

    @property
    def template_status(self):
        return 'Active' if self.is_active else 'Archived'

    @property
    def template_type_verbose(self):
        return dict(Template.TYPES)[self.template_type]

    @property
    def application_domain_verbose(self):
        return dict(Template.DOMAINS)[self.application_domain]

    class Meta:
        ordering = ('-is_active', )

    # Default display fields on the listing page of the model
    class Display:
        display = [
            'template_name', 'application_domain_verbose',
            'template_type_verbose', 'template_status'
        ]
        labels = [
            'Template Name', 'Application Domain', 'Template Type',
            'Template Status'
        ]
        #  Display actions
        edit = True
        view = True
        archive = True


class Unit(models.Model):
    unit_type = models.CharField(max_length=20, blank=False, null=False)
    description = models.CharField(max_length=100, blank=False, null=False)
    short_description = models.CharField(max_length=30,
                                         blank=False,
                                         null=False)
    hmrc_code = models.IntegerField(blank=False, null=False)

    def __str__(self):
        return self.description


class CommodityType(models.Model):
    type_code = models.CharField(max_length=20, blank=False, null=False)
    type = models.CharField(max_length=50, blank=False, null=False)

    def __str__(self):
        return self.type


class Commodity(Archivable, models.Model):
    TEXTILES = 'TEXTILES'
    IRON_STEEL = 'IRON_STEEL'
    FIREARMS_AMMO = 'FIREARMS_AMMO'
    WOOD = 'WOOD'
    VEHICLES = 'VEHICLES'
    WOOD_CHARCOAL = 'WOOD_CHARCOAL'
    PRECIOUS_METAL_STONE = 'PRECIOUS_METAL_STONE'
    OIL_PETROCHEMICALS = 'OIL_PETROCHEMICALS'

    is_active = models.BooleanField(blank=False, null=False, default=True)
    start_datetime = models.DateTimeField(auto_now_add=True,
                                          blank=False,
                                          null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)
    commodity_code = models.CharField(max_length=10, blank=False, null=False)
    validity_start_date = models.DateField(blank=False, null=True)
    validity_end_date = models.DateField(blank=True, null=True)
    quantity_threshold = models.IntegerField(blank=True, null=True)
    sigl_product_type = models.CharField(max_length=3, blank=True, null=True)

    @property
    def commodity_type_verbose(self):
        return self.commodity_type.type

    class Meta:
        ordering = ('commodity_code', )

    class Display:
        display = [
            'commodity_code', 'commodity_type_verbose',
            ('validity_start_date', 'validity_end_date')
        ]
        labels = ['Commodity Code', 'Commodity Type', 'Validity']
        view = False
        edit = True
        archive = True


class CommodityGroup(Archivable, models.Model):
    AUTO = 'AUTO'
    CATEGORY = 'CATEGORY'

    TYPES = ((AUTO, 'Auto'), (CATEGORY, ('Category')))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    start_datetime = models.DateTimeField(blank=False, null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)
    group_type = models.CharField(max_length=20,
                                  choices=TYPES,
                                  blank=False,
                                  null=False,
                                  default=AUTO)
    group_code = models.CharField(max_length=25, blank=False, null=False)
    group_name = models.CharField(max_length=100, blank=True, null=True)
    group_description = models.CharField(max_length=4000,
                                         blank=True,
                                         null=True)
    commodity_type = models.ForeignKey(CommodityType,
                                       on_delete=models.PROTECT,
                                       blank=True,
                                       null=True)
    unit = models.ForeignKey(Unit,
                             on_delete=models.SET_NULL,
                             blank=True,
                             null=True)
    commodities = models.ManyToManyField(Commodity, blank=True)

    @property
    def group_type_verbose(self):
        return dict(CommodityGroup.TYPES)[self.group_type]

    @property
    def commodity_type_verbose(self):
        return self.commodity_type.type

    class Display:
        display = [
            'group_type_verbose', 'commodity_type_verbose', 'group_code',
            'group_description'
        ]
        labels = [
            'Commodity Code', 'Commodity Type', 'Group Code/ Group Name',
            'Descripption/ Commodities'
        ]
        view = False
        edit = True
        archive = True


class Country(models.Model):
    SOVEREIGN_TERRITORY = 'SOVEREIGN_TERRITORY'
    SYSTEM = 'SYSTEM'

    TYPES = ((SOVEREIGN_TERRITORY, 'Sovereign Territory'), (SYSTEM, 'System'))

    name = models.CharField(max_length=4000, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    type = models.CharField(max_length=30,
                            choices=TYPES,
                            blank=False,
                            null=False)
    commission_code = models.CharField(max_length=20, blank=False, null=False)
    hmrc_code = models.CharField(max_length=20, blank=False, null=False)

    @property
    def name_slug(self):
        return self.name.lower().replace(' ', '_')

    class Meta:
        ordering = ('name', )


class CountryGroup(models.Model):
    name = models.CharField(max_length=4000, blank=False, null=False)
    comments = models.CharField(max_length=4000, blank=True, null=True)
    countries = models.ManyToManyField(Country,
                                       blank=True,
                                       related_name='country_groups')

    class Meta:
        ordering = ('name', )


class CountryTranslationSet(Archivable, models.Model):
    name = models.CharField(max_length=100, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)

    class Display:
        archive = True


class CountryTranslation(models.Model):
    translation = models.CharField(max_length=150, blank=False, null=False)
    country = models.ForeignKey(Country,
                                on_delete=models.CASCADE,
                                blank=False,
                                null=False)
    translation_set = models.ForeignKey(CountryTranslationSet,
                                        on_delete=models.CASCADE,
                                        blank=False,
                                        null=False)

    class Display:
        archive = True


class ProductLegislation(Archivable, models.Model):
    name = models.CharField(max_length=500, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    is_biocidal = models.BooleanField(blank=False, null=False, default=False)
    is_eu_cosmetics_regulation = models.BooleanField(blank=False,
                                                     null=False,
                                                     default=False)
    is_biocidal_claim = models.BooleanField(blank=False,
                                            null=False,
                                            default=False)

    @property
    def is_biocidal_yes_no(self):
        return 'Yes' if self.is_biocidal else 'No'

    @property
    def is_biocidal_claim_yes_no(self):
        return 'Yes' if self.is_biocidal_claim else 'No'

    @property
    def is_eu_cosmetics_regulation_yes_no(self):
        return 'Yes' if self.is_eu_cosmetics_regulation else 'No'

    class Meta:
        ordering = ('name', )

    class Display:
        display = [
            'name', 'is_biocidal_yes_no', 'is_biocidal_claim_yes_no',
            'is_eu_cosmetics_regulation_yes_no'
        ]
        labels = [
            'legislation Name', 'Is Biocidal', 'Is Biocidal Claim',
            'Is EU Cosmetics Regulation'
        ]
        view = True
        edit = True
        archive = True


class ObsoleteCalibreGroup(Archivable, Sortable, models.Model):
    name = models.CharField(max_length=200, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    order = models.IntegerField(blank=False, null=False)

    class Meta:
        ordering = ('order', )

    class Display:
        display = ['name', 'calibres__count']
        #  TODO: Change labels to dictionary with display fields as keys
        labels = ['Obsolete Calibre Group Name', 'Number of Items']
        #  TODO: Change help text keys to field names rather than label
        help_texts = {
            'Number of Items':
            'The total number of obsolete calibres in this group'
        }
        view = True
        edit = True
        archive = True
        sort = True


class ObsoleteCalibre(Archivable, models.Model):
    calibre_group = models.ForeignKey(ObsoleteCalibreGroup,
                                      on_delete=models.CASCADE,
                                      blank=False,
                                      null=False,
                                      related_name='calibres')
    name = models.CharField(max_length=200, blank=False, null=False)
    is_active = models.BooleanField(blank=False, null=False, default=True)
    order = models.IntegerField(blank=False, null=False)

    @property
    def status(self):
        if not self.id:
            return 'Pending'
        elif not self.is_active:
            return 'Archvied'
        else:
            return 'Current'

    class Meta:
        ordering = ('order', )


class Office(models.Model):
    """Office for importer/exporters"""

    # Address Entry type
    MANUAL = "MANUAL"
    SEARCH = "SEARCH"
    EMPTY = "EMPTY"
    ENTRY_TYPES = ((MANUAL, 'Manual'), (SEARCH, 'Search'), (EMPTY, 'Empty'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    postcode = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=4000, blank=False, null=True)
    eori_number = models.CharField(max_length=20, blank=True, null=True)
    address_entry_type = models.CharField(max_length=10,
                                          blank=False,
                                          null=False,
                                          default=EMPTY)


class Importer(Archivable, BaseTeam):
    # Regions
    INDIVIDUAL = "INDIVIDUAL"
    ORGANISATION = "ORGANISATION"
    TYPES = ((INDIVIDUAL, "Individual"), (ORGANISATION, "Organisation"))

    # Region Origins
    UK = None
    EUROPE = "E"
    NON_EUROPEAN = "O"
    REGIONS = ((UK, "UK"), (EUROPE, 'Europe'), (NON_EUROPEAN, 'Non-European'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    type = models.CharField(max_length=20,
                            choices=TYPES,
                            blank=False,
                            null=False)
    # Organisation's name
    name = models.CharField(max_length=4000, blank=True, null=True)
    registered_number = models.CharField(max_length=15, blank=True, null=True)
    eori_number = models.CharField(max_length=20, blank=True, null=True)
    region_origin = models.CharField(max_length=1,
                                     choices=REGIONS,
                                     blank=True,
                                     null=True)
    comments = models.CharField(max_length=4000, blank=True, null=True)
    offices = models.ManyToManyField(Office)
    # Having a main importer means importer is an agent
    main_importer = models.ForeignKey("self",
                                      on_delete=models.SET_NULL,
                                      blank=True,
                                      null=True,
                                      related_name='agents')
    user = models.ForeignKey(User,
                             on_delete=models.SET_NULL,
                             blank=True,
                             null=True,
                             related_name='own_importers')

    def is_agent(self):
        return self.main_importer is not None

    @property
    def entity_type(self):
        return dict(Importer.TYPES)[self.type]

    class Display:
        display = [('full_name', 'registered_number', 'entity_type')]
        labels = ['Importer Name / Importer Reg No / Importer Entity Type']
        edit = True
        view = True
        archive = True


class Exporter(Archivable, BaseTeam):

    is_active = models.BooleanField(blank=False, null=False, default=True)
    name = models.CharField(max_length=4000, blank=False, null=False)
    registered_number = models.CharField(max_length=15, blank=True, null=True)
    comments = models.CharField(max_length=4000, blank=True, null=True)
    offices = models.ManyToManyField(Office)
    # Having a main exporter means exporter is an agent
    main_exporter = models.ForeignKey("self",
                                      on_delete=models.SET_NULL,
                                      blank=True,
                                      null=True,
                                      related_name='agents')

    def is_agent(self):
        return self.main_importer is not None

    class Display:
        display = ['name']
        labels = ['Exporter Name']
        edit = True
        view = True
        archive = True


class FirearmsAuthority(models.Model):
    DEACTIVATED_FIREARMS = 'DEACTIVATED'
    FIREARMS = 'FIREARMS'
    REGISTERED_FIREARMS_DEALER = 'RFD'
    SHOTGUN = 'SHOTGUN'

    # Address Entry type
    MANUAL = "MANUAL"
    SEARCH = "SEARCH"
    ENTRY_TYPES = ((MANUAL, 'Manual'), (SEARCH, 'Search'))

    CERTIFICATE_TYPES = ((DEACTIVATED_FIREARMS, 'Deactivation Certificate'),
                         (FIREARMS, 'Firearms Certificate'),
                         (REGISTERED_FIREARMS_DEALER,
                          'Registered Firearms Dealer Certificate'),
                         (SHOTGUN, 'Shotgun Certificate'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    reference = models.CharField(max_length=50, blank=False, null=True)
    certificate_type = models.CharField(max_length=20,
                                        choices=CERTIFICATE_TYPES,
                                        blank=False,
                                        null=False)
    postcode = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=300, blank=False, null=False)
    address_entry_type = models.CharField(max_length=10,
                                          blank=False,
                                          null=False,
                                          default=MANUAL)
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    further_details = models.CharField(max_length=4000, blank=True, null=True)
    issuing_constabulary = models.ForeignKey(Constabulary,
                                             on_delete=models.PROTECT,
                                             blank=False,
                                             null=False)
    linked_offices = models.ManyToManyField(Office)
    importer = models.ForeignKey(Importer,
                                 on_delete=models.PROTECT,
                                 blank=False,
                                 null=False,
                                 related_name='firearms_authorities')


class Section5Authority(models.Model):
    # Address Entry type
    MANUAL = "MANUAL"
    SEARCH = "SEARCH"
    ENTRY_TYPES = ((MANUAL, 'Manual'), (SEARCH, 'Search'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    reference = models.CharField(max_length=50, blank=False, null=True)
    postcode = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=300, blank=False, null=False)
    address_entry_type = models.CharField(max_length=10,
                                          blank=False,
                                          null=False,
                                          default=MANUAL)
    start_date = models.DateField(blank=False, null=False)
    end_date = models.DateField(blank=False, null=False)
    further_details = models.CharField(max_length=4000, blank=True, null=True)
    linked_offices = models.ManyToManyField(Office)
    importer = models.ForeignKey(Importer,
                                 on_delete=models.PROTECT,
                                 blank=False,
                                 null=False,
                                 related_name='section5_authorities')


class AccessRequest(models.Model):

    # Request types
    IMPORTER = "MAIN_IMPORTER_ACCESS"
    IMPORTER_AGENT = "AGENT_IMPORTER_ACCESS"
    EXPORTER = "MAIN_EXPORTER_ACCESS"
    EXPORTER_AGENT = "AGENT_EXPORTER_ACCESS"

    REQUEST_TYPES = (
        (IMPORTER, 'Request access to act as an Importer'),
        (IMPORTER_AGENT, 'Request access to act as an Agent for an Importer'),
        (EXPORTER, 'Request access to act as an Exporter'),
        (EXPORTER_AGENT, 'Request access to act as an Agent for an Exporter'),
    )

    # Access Request status
    SUBMITTED = 'SUBMITTED'
    CLOSED = 'CLOSED'
    STATUSES = ((SUBMITTED, 'Submitted'), (CLOSED, 'Closed'))

    # Access Request response
    APPROVED = 'APPROVED'
    REFUSED = 'REFUSED'
    RESPONSES = ((APPROVED, 'Approved'), (REFUSED, 'Refused'))

    objects = AccessRequestQuerySet.as_manager()
    reference = models.CharField(max_length=50, blank=False, null=False)
    request_type = models.CharField(max_length=30,
                                    choices=REQUEST_TYPES,
                                    blank=False,
                                    null=False)
    status = models.CharField(max_length=30,
                              choices=STATUSES,
                              blank=False,
                              null=False,
                              default=SUBMITTED)
    organisation_name = models.CharField(max_length=100,
                                         blank=False,
                                         null=False)
    organisation_address = models.CharField(max_length=500,
                                            blank=False,
                                            null=True)
    request_reason = models.CharField(max_length=1000, blank=False, null=True)
    agent_name = models.CharField(max_length=100, blank=False, null=True)
    agent_address = models.CharField(max_length=500, blank=False, null=True)
    submit_datetime = models.DateTimeField(auto_now_add=True,
                                           blank=False,
                                           null=False)
    submitted_by = models.ForeignKey(User,
                                     on_delete=models.PROTECT,
                                     blank=False,
                                     null=False,
                                     related_name='submitted_access_requests')
    last_update_datetime = models.DateTimeField(auto_now=True,
                                                blank=False,
                                                null=False)
    last_updated_by = models.ForeignKey(User,
                                        on_delete=models.PROTECT,
                                        blank=True,
                                        null=True,
                                        related_name='updated_access_requests')
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(User,
                                  on_delete=models.PROTECT,
                                  blank=True,
                                  null=True,
                                  related_name='closed_access_requests')
    response = models.CharField(max_length=20,
                                choices=RESPONSES,
                                blank=False,
                                null=True)
    response_reason = models.CharField(max_length=4000, blank=True, null=True)
    linked_importer = models.ForeignKey(Importer,
                                        on_delete=models.PROTECT,
                                        blank=True,
                                        null=True,
                                        related_name='access_requests')
    linked_exporter = models.ForeignKey(Exporter,
                                        on_delete=models.PROTECT,
                                        blank=True,
                                        null=True,
                                        related_name='access_requests')

    def request_type_verbose(self):
        return dict(AccessRequest.REQUEST_TYPES)[self.request_type]

    def request_type_short(self):
        if self.request_type in [self.IMPORTER, self.IMPORTER_AGENT]:
            return "Import Access Request"
        else:
            return "Exporter Access Request"


class ApprovalRequest(models.Model):
    """
    Approval request for submitted requests.
    Approval requests are requested from importer/exporter
    contacts by case officers
    """

    # Approval Request response options
    APPROVE = 'APPROVE'
    REFUSE = 'REFUSE'
    RESPONSE_OPTIONS = ((APPROVE, 'Approve'), (REFUSE, 'Refuse'))

    # Approval Request status
    DRAFT = 'DRAFT'
    COMPLETED = 'COMPLETED'
    STATUSES = ((DRAFT, 'DRAFT'), (REFUSE, 'OPEN'))

    access_request = models.ForeignKey(AccessRequest,
                                       on_delete=models.CASCADE,
                                       blank=False,
                                       null=False)
    status = models.CharField(max_length=20,
                              choices=STATUSES,
                              blank=True,
                              null=True)
    request_date = models.DateTimeField(blank=True, null=True)
    requested_by = models.ForeignKey(User,
                                     on_delete=models.CASCADE,
                                     blank=True,
                                     null=True,
                                     related_name='approval_requests')
    requested_from = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='assigned_approval_requests')
    response = models.CharField(max_length=20,
                                choices=RESPONSE_OPTIONS,
                                blank=True,
                                null=True)
    response_by = models.ForeignKey(User,
                                    on_delete=models.CASCADE,
                                    blank=True,
                                    null=True,
                                    related_name='responded_approval_requests')
    response_date = models.DateTimeField(blank=True, null=True)
    response_reason = models.CharField(max_length=4000, blank=True, null=True)


class AccessRequestProcess(Process):
    access_request = models.ForeignKey(AccessRequest, on_delete=models.CASCADE)
    objects = ProcessQuerySet.as_manager()


class ImportApplicationType(models.Model):
    is_active = models.BooleanField(blank=False, null=False)
    type_code = models.CharField(max_length=30, blank=False, null=False)
    type = models.CharField(max_length=70, blank=False, null=False)
    sub_type_code = models.CharField(max_length=30, blank=False, null=False)
    sub_type = models.CharField(max_length=70, blank=True, null=True)
    licent_type_code = models.CharField(max_length=20, blank=False, null=False)
    sigl_flag = models.BooleanField(blank=False, null=False)
    chief_flag = models.BooleanField(blank=False, null=False)
    chief_licence_prefix = models.CharField(max_length=10,
                                            blank=True,
                                            null=True)
    paper_licence_flag = models.BooleanField(blank=False, null=False)
    electronic_licence_flag = models.BooleanField(blank=False, null=False)
    cover_letter_flag = models.BooleanField(blank=False, null=False)
    cover_letter_schedule_flag = models.BooleanField(blank=False, null=False)
    category_flag = models.BooleanField(blank=False, null=False)
    sigl_category_prefix = models.CharField(max_length=100,
                                            blank=True,
                                            null=True)
    chief_category_prefix = models.CharField(max_length=10,
                                             blank=True,
                                             null=True)
    default_licence_length_months = models.IntegerField(blank=True, null=True)
    endorsements_flag = models.BooleanField(blank=False, null=False)
    default_commodity_desc = models.CharField(max_length=200,
                                              blank=True,
                                              null=True)
    quantity_unlimited_flag = models.BooleanField(blank=False, null=False)
    unit_list_csv = models.CharField(max_length=200, blank=True, null=True)
    exp_cert_upload_flag = models.BooleanField(blank=False, null=False)
    supporting_docs_upload_flag = models.BooleanField(blank=False, null=False)
    multiple_commodities_flag = models.BooleanField(blank=False, null=False)
    guidance_file_url = models.CharField(max_length=4000,
                                         blank=True,
                                         null=True)
    licence_category_description = models.CharField(max_length=1000,
                                                    blank=True,
                                                    null=True)

    usage_auto_category_desc_flag = models.BooleanField(blank=False,
                                                        null=False)
    case_checklist_flag = models.BooleanField(blank=False, null=False)
    importer_printable = models.BooleanField(blank=False, null=False)
    origin_country_group = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='application_types_from')
    consignment_country_group = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='application_types_to')
    master_country_group = models.ForeignKey(CountryGroup,
                                             on_delete=models.PROTECT,
                                             blank=True,
                                             null=True,
                                             related_name='application_types')
    commodity_type = models.ForeignKey(CommodityType,
                                       on_delete=models.PROTECT,
                                       blank=True,
                                       null=True)
    declaration_template = models.ForeignKey(
        Template,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name='declaration_application_types')
    endorsements = models.ManyToManyField(
        Template, related_name='endorsement_application_types')
    default_commodity_group = models.ForeignKey(CommodityGroup,
                                                on_delete=models.PROTECT,
                                                blank=True,
                                                null=True)


class ImportApplication(models.Model):

    is_active = models.BooleanField(blank=False, null=False, default=True)
    application_type = models.ForeignKey(ImportApplicationType,
                                         on_delete=models.PROTECT,
                                         blank=False,
                                         null=False)
    applicant_reference = models.CharField(max_length=500,
                                           blank=True,
                                           null=True)
    submit_datetime = models.DateTimeField(blank=True, null=True)
    create_datetime = models.DateTimeField(blank=False,
                                           null=False,
                                           auto_now_add=True)
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='submitted_import_applications')
    created_by = models.ForeignKey(User,
                                   on_delete=models.PROTECT,
                                   blank=False,
                                   null=False,
                                   related_name='created_import_applications')
    importer = models.ForeignKey(Importer,
                                 on_delete=models.PROTECT,
                                 blank=False,
                                 null=False,
                                 related_name='import_applications')
    importer_office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        blank=False,
        null=True,
        related_name='office_import_applications')
    contact = models.ForeignKey(User,
                                on_delete=models.PROTECT,
                                blank=True,
                                null=True,
                                related_name='contact_import_applications')
    origin_country = models.ForeignKey(Country,
                                       on_delete=models.PROTECT,
                                       blank=True,
                                       null=True,
                                       related_name='import_applications_from')
    consignment_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='import_applications_to')


class ImportCase(models.Model):
    IN_PROGRESS = 'IN_PROGRESS'
    SUBMITTED = 'SUBMITTED'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    WITHDRAWN = 'WITHDRAWN'
    STOPPED = 'STOPPED'
    VARIATION_REQUESTED = 'VARIATION_REQUESTED'
    REVOKED = 'REVOKED'
    DELETED = 'DELETED'

    STATUSES = ((IN_PROGRESS, 'In Progress'), (SUBMITTED, 'Submitted'),
                (PROCESSING, 'Processing'), (COMPLETED, 'Completed'),
                (WITHDRAWN, 'Withdrawn'), (STOPPED, 'Stopped'),
                (REVOKED, 'Revoked'), (VARIATION_REQUESTED,
                                       'Variation Requested'), (DELETED,
                                                                'Deleted'))

    # Chief usage status
    CANCELLED = 'C'
    EXHAUSTED = 'E'
    EXPIRED = 'D'
    SURRENDERED = 'S'
    CHIEF_STATUSES = ((CANCELLED, 'Cancelled'), (EXHAUSTED, 'Exhausted'),
                      (EXPIRED, 'Expired'), (SURRENDERED, 'S'))

    # Decision
    REFUSE = 'REFUSE'
    APPROVE = 'APPROVE'
    DECISIONS = ((REFUSE, 'Refuse'), (APPROVE, 'Approve'))

    application = models.OneToOneField(ImportApplication,
                                       on_delete=models.PROTECT,
                                       related_name='case')
    status = models.CharField(max_length=30,
                              choices=STATUSES,
                              blank=False,
                              null=False)
    reference = models.CharField(max_length=50, blank=True, null=True)
    variation_no = models.IntegerField(blank=False, null=False, default=0)
    legacy_case_flag = models.BooleanField(blank=False,
                                           null=False,
                                           default=False)
    chief_usage_status = models.CharField(max_length=1,
                                          choices=CHIEF_STATUSES,
                                          blank=True,
                                          null=True)
    under_appeal_flag = models.BooleanField(blank=False,
                                            null=False,
                                            default=False)
    decision = models.CharField(max_length=10,
                                choices=DECISIONS,
                                blank=True,
                                null=True)
    variation_decision = models.CharField(max_length=10,
                                          choices=DECISIONS,
                                          blank=True,
                                          null=True)
    refuse_reason = models.CharField(max_length=4000, blank=True, null=True)
    variation_refuse_reason = models.CharField(max_length=4000,
                                               blank=True,
                                               null=True)
    issue_date = models.DateField(blank=True, null=True)
    licence_start_date = models.DateField(blank=True, null=True)
    licence_end_date = models.DateField(blank=True, null=True)
    licence_extended_flag = models.BooleanField(blank=False,
                                                null=False,
                                                default=False)
    last_update_datetime = models.DateTimeField(blank=False,
                                                null=False,
                                                auto_now=True)
    last_updated_by = models.ForeignKey(User,
                                        on_delete=models.PROTECT,
                                        blank=False,
                                        null=False,
                                        related_name='updated_import_cases')


class CaseConstabularyEmail(models.Model):

    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    DRAFT = 'DRAFT'
    STATUSES = ((OPEN, 'Open'), (CLOSED, 'Closed'), (DRAFT, 'Draft'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    case = models.ForeignKey(ImportCase,
                             on_delete=models.PROTECT,
                             blank=False,
                             null=False)
    status = models.CharField(max_length=30,
                              blank=False,
                              null=False,
                              default=DRAFT)
    email_cc_address_list = models.CharField(max_length=4000,
                                             blank=True,
                                             null=True)
    email_subject = models.CharField(max_length=100, blank=True, null=True)
    email_body = models.CharField(max_length=4000, blank=True, null=True)
    email_sent_datetime = models.DateTimeField(blank=True, null=True)
    email_closed_datetime = models.DateTimeField(blank=True, null=True)


class ImportCaseVariation(models.Model):

    OPEN = 'OPEN'
    DRAFT = 'DRAFT'
    CANCELLED = 'CANCELLED'
    REJECTED = 'REJECTED'
    ACCEPTED = 'ACCEPTED'
    WITHDRAWN = 'WITHDRAWN'

    STATUSES = ((DRAFT, 'Draft'), (OPEN, 'Open'), (CANCELLED, 'Cancelled'),
                (REJECTED, 'Rejected'), (ACCEPTED, 'Accepted'), (WITHDRAWN,
                                                                 'Withdrawn'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(max_length=30,
                              choices=STATUSES,
                              blank=False,
                              null=False)
    case = models.ForeignKey(ImportCase,
                             on_delete=models.PROTECT,
                             blank=False,
                             null=False)
    extension_flag = models.BooleanField(blank=False,
                                         null=False,
                                         default=False)
    requested_date = models.DateField(blank=True, null=True, auto_now_add=True)
    requested_by = models.ForeignKey(User,
                                     on_delete=models.PROTECT,
                                     blank=True,
                                     null=True)
    what_varied = models.CharField(max_length=4000, blank=True, null=True)
    why_varied = models.CharField(max_length=4000, blank=True, null=True)
    when_varied = models.DateField(blank=True, null=True)
    reject_reason = models.CharField(max_length=4000, blank=True, null=True)
    closed_date = models.DateField(blank=True, null=True)
