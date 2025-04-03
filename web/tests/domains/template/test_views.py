from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertInHTML, assertRedirects

from web.domains.template.constants import TemplateCodes
from web.domains.template.views import UnknownTemplateTypeException
from web.models import Country, ImportApplicationType, Template
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.views.actions import ArchiveTemplate, Unarchive, UnarchiveTemplate


class TestTemplateListView(AuthTestCase):
    url = "/template/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == "Maintain Templates"

    def test_number_of_pages(self):
        response = self.ilb_admin_client.get(self.url, {"template_name_title": ""})
        page = response.context_data["page"]
        assert page.paginator.num_pages == 2

    def test_page_results(self):
        response = self.ilb_admin_client.get(self.url, {"page": "2", "template_name_title": ""})
        page = response.context_data["page"]
        assert len(page.object_list) == 41

    def test_email_template_not_archivable(self):
        response = self.ilb_admin_client.get(self.url, {"template_type": "EMAIL_TEMPLATE"})
        page = response.context_data["page"]
        for _template in page.object_list:
            assert ArchiveTemplate().display(_template) is False
            assert UnarchiveTemplate().display(_template) is False

    def test_archived_not_editable(self):
        """Making sure that the only visible action for archived templates is the unarchive action"""
        new_constabulary = Template.objects.filter(is_active=False).first()
        response = self.ilb_admin_client.get(self.url)
        for action in response.context_data["display"].actions:
            if action.display(new_constabulary) is True:
                assert isinstance(action, Unarchive)


class TestEndorsementCreateView(AuthTestCase):
    url = "/template/endorsement/new/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == "New Endorsement"

    def test_form_valid(self):
        assert not Template.objects.filter(
            template_type=Template.ENDORSEMENT,
            template_name="Test name",
            versions__content="Test content",
        ).exists()
        response = self.ilb_admin_client.post(
            self.url, {"template_name": "Test name", "content": "Test content"}
        )
        assert response.status_code == HTTPStatus.FOUND
        template = Template.objects.get(
            template_type=Template.ENDORSEMENT,
            template_name="Test name",
            versions__content="Test content",
        )
        assert template.template_name == "Test name"
        assert template.template_content == "Test content"
        assert template.version_no == 1


class TestTemplateEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.template = Template.objects.filter(is_active=True).first()
        self.url = f"/template/{self.template.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assertInHTML(f"Editing {self.template}", response.content.decode())

    def test_invalid_post_data(self):
        response = self.ilb_admin_client.post(self.url, data={"test": "test"})
        assert response.status_code == HTTPStatus.OK
        assertContains(response, "You must enter this item")


@pytest.mark.parametrize(
    "t_type,t_code",
    [
        (Template.DECLARATION, TemplateCodes.IMA_WD_DECLARATION),
        (Template.EMAIL_TEMPLATE, TemplateCodes.IMA_SANCTIONS_EMAIL),
        (Template.LETTER_TEMPLATE, TemplateCodes.COVER_FIREARMS_ANTI_PERSONNEL_MINES),
        (Template.LETTER_FRAGMENT, TemplateCodes.FIREARMS_MARKINGS_STANDARD),
    ],
)
def test_edit_template(t_type, t_code, ilb_admin_client):
    template = Template.objects.get(template_type=t_type, template_code=t_code)
    version_no = template.version_no + 1
    data = {"template_name": "Test name", "content": "Test content"}

    if t_type == Template.EMAIL_TEMPLATE:
        data = data | {"title": "Test Title"}

    ilb_admin_client.post(f"/template/{template.id}/edit/", data=data)

    template.refresh_from_db()
    assert template.version_no == version_no
    assert template.template_name == "Test name"
    assert template.template_content == "Test content"

    if t_type == Template.EMAIL_TEMPLATE:
        assert template.template_title == "Test Title"

    # Test submitting identical info does not create a new version
    ilb_admin_client.post(f"/template/{template.id}/edit/", data=data)

    template.refresh_from_db()
    assert template.version_no == version_no
    assert template.template_name == "Test name"
    assert template.template_content == "Test content"

    if t_type == Template.EMAIL_TEMPLATE:
        assert template.template_title == "Test Title"


def test_edit_unknown_template_type(ilb_admin_client):
    template = Template.objects.filter(template_type="CFS_SCHEDULE").first()
    with pytest.raises(
        UnknownTemplateTypeException, match=f"Unknown template type '{template.template_type}'"
    ):
        ilb_admin_client.post(f"/template/{template.id}/edit/", data={"title": "Test Title"})


class TestTemplateDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.template = Template.objects.filter(is_active=True).first()
        self.url = f"/template/{self.template.id}/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assertInHTML(f"Viewing {self.template}", response.content.decode())


@pytest.mark.parametrize(
    "t_type,t_code",
    [
        (Template.CFS_SCHEDULE, TemplateCodes.CFS_SCHEDULE_ENGLISH),
        (Template.CFS_SCHEDULE_TRANSLATION, TemplateCodes.CFS_SCHEDULE_TRANSLATION),
    ],
)
def test_view_cfs_templates(t_type, t_code, ilb_admin_client):
    template = Template.objects.get(template_type=t_type, template_code=t_code)
    response = ilb_admin_client.get(f"/template/{template.id}/")
    assert response.status_code == HTTPStatus.OK


class TestCFSDeclarationTranslation(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.create_url = reverse("template-cfs-declaration-translation-new")
        self.template = Template.objects.filter(
            template_type=Template.CFS_DECLARATION_TRANSLATION, is_active=True
        ).first()
        self.edit_url = reverse(
            "template-cfs-declaration-translation-edit",
            kwargs={"pk": self.template.pk},
        )

    def test_get_create_new_declaration_translation_page(self):
        response = self.ilb_admin_client.get(self.create_url)
        assertContains(response, "CFS Declaration Translation Name")

    def test_create_new_declaration_translation_invalid(self):
        response = self.ilb_admin_client.post(
            self.create_url,
            data={
                "template_name": "Test template",
                "countries": [],
                "content": "Test translation content",
            },
        )
        assert response.status_code == HTTPStatus.OK

    def test_create_new_declaration_translation(self):
        country_pks = Country.objects.values_list("pk", flat=True)[:3]
        response = self.ilb_admin_client.post(
            self.create_url,
            data={
                "template_name": "Test template",
                "countries": list(country_pks),
                "content": "Test translation content",
            },
            follow=True,
        )
        assertContains(response, "Currently editing version 1")

        template = Template.objects.get(
            template_type=Template.CFS_DECLARATION_TRANSLATION,
            template_name="Test template",
            versions__content="Test translation content",
        )
        assert template.version_no == 1
        assert template.template_content == "Test translation content"
        assert list(template.countries.values_list("pk", flat=True)) == list(country_pks)

    def test_get_edit_declaration_translation_page(self):
        response = self.ilb_admin_client.get(self.edit_url)
        assertContains(response, "CFS Declaration Translation Name")

    def test_edit_cfs_declaration_translation(self):
        version_number = self.template.version_no
        country_pks = Country.objects.values_list("pk", flat=True)[:3]
        response = self.ilb_admin_client.post(
            self.edit_url,
            data={
                "template_name": "Test template",
                "countries": list(country_pks),
                "content": "Test translation content",
            },
            follow=True,
        )
        assertContains(response, f"Currently editing version {version_number + 1}")
        self.template.refresh_from_db()

        assert self.template.version_no == version_number + 1
        assert self.template.template_name == "Test template"
        assert self.template.template_content == "Test translation content"

    def test_edit_cfs_declaration_translation_invalid(self):
        version_number = self.template.version_no
        response = self.ilb_admin_client.post(
            self.edit_url,
            data={
                "template_name": "Test template",
                "countries": [],
                "content": "Test translation content",
            },
            follow=True,
        )
        assertContains(response, f"Currently editing version {version_number}")
        self.template.refresh_from_db()

        assert self.template.version_no == version_number
        assert self.template.template_name != "Test template"
        assert self.template.template_content != "Test translation content"


class TestCFSScheduleTranslation(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.create_url = reverse("template-cfs-schedule-translation-new")
        self.template = Template.objects.filter(
            template_type=Template.CFS_SCHEDULE_TRANSLATION, is_active=True
        ).first()
        self.country_pks = list(self.template.countries.values_list("pk", flat=True))
        self.edit_url = reverse(
            "template-cfs-schedule-translation-edit",
            kwargs={"pk": self.template.pk},
        )

    def test_get_create_new_schedule_translation_page(self):
        response = self.ilb_admin_client.get(self.create_url)
        assertContains(response, "CFS Schedule Translation Name")

    def test_create_new_schedule_translation_invalid(self):
        response = self.ilb_admin_client.post(
            self.create_url,
            data={
                "template_name": "Test template",
                "countries": self.country_pks,
                "country_translation_set": 1,
            },
        )
        assert response.status_code == HTTPStatus.OK
        assertContains(response, "These countries already have the CFS Schedule translated")

    def test_create_new_schedule_translation(self):
        country_pks = Country.objects.exclude(pk__in=self.country_pks).values_list("pk", flat=True)[
            :3
        ]
        response = self.ilb_admin_client.post(
            self.create_url,
            data={
                "template_name": "Test template",
                "countries": list(country_pks),
                "country_translation_set": 1,
            },
        )
        assert response.status_code == HTTPStatus.FOUND
        template = Template.objects.get(
            template_type=Template.CFS_SCHEDULE_TRANSLATION,
            template_name="Test template",
            country_translation_set_id=1,
        )
        assert template.template_name == "Test template"
        assert list(template.countries.values_list("pk", flat=True)) == list(country_pks)

    def test_get_edit_schedule_translation_page(self):
        response = self.ilb_admin_client.get(self.edit_url)
        assertContains(response, "CFS Schedule Translation Name")

    def test_edit_cfs_schedule_translation(self):
        country_pks = Country.objects.exclude(pk__in=self.country_pks).values_list("pk", flat=True)[
            :3
        ]
        response = self.ilb_admin_client.post(
            self.edit_url,
            data={
                "template_name": "Test template",
                "countries": list(country_pks),
                "country_translation_set": self.template.country_translation_set_id,
            },
        )
        assert response.status_code == HTTPStatus.FOUND
        self.template.refresh_from_db()

        assert self.template.template_name == "Test template"
        assert list(self.template.countries.values_list("pk", flat=True)) == list(country_pks)

    def test_edit_cfs_schedule_translation_invalid(self):
        self.ilb_admin_client.post(
            self.edit_url,
            data={
                "template_name": "Test template",
                "countries": [],
                "country_translation_set": "Test translation content",
            },
        )
        self.template.refresh_from_db()

        assert self.template.template_name != "Test template"


class TestCFSScheduleParagraphs(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.template = Template.objects.filter(
            template_type=Template.CFS_SCHEDULE_TRANSLATION, is_active=True
        ).first()
        self.url = reverse(
            "template-cfs-schedule-translation-paragraphs-edit", kwargs={"pk": self.template.pk}
        )
        self.paragraph_data = {
            "para_SCHEDULE_HEADER": "test schedule header",
            "para_SCHEDULE_INTRODUCTION": "test schedule introduction [[EXPORTER_ADDRESS_FLAT]] [[EXPORTER_NAME]]",
            "para_IS_MANUFACTURER": "test is manufacturer",
            "para_IS_NOT_MANUFACTURER": "test is not manufacturer",
            "para_EU_COSMETICS_RESPONSIBLE_PERSON": "test eu cosmetics",
            "para_EU_COSMETICS_RESPONSIBLE_PERSON_NI": "test eu cosmetics ni",
            "para_LEGISLATION_STATEMENT": "test legislation statement",
            "para_ELIGIBILITY_ON_SALE": "test on sale",
            "para_ELIGIBILITY_MAY_BE_SOLD": "test may be sold",
            "para_GOOD_MANUFACTURING_PRACTICE": "test good manufacturing practice",
            "para_GOOD_MANUFACTURING_PRACTICE_NI": "test good maufacturing practice ni",
            "para_COUNTRY_OF_MAN_STATEMENT": "test country of manufacture statement [[COUNTRY_OF_MANUFACTURE]]",
            "para_COUNTRY_OF_MAN_STATEMENT_WITH_NAME": "test country of manufacture statement name [[MANUFACTURED_AT_NAME]] [[COUNTRY_OF_MANUFACTURE]]",
            "para_COUNTRY_OF_MAN_STATEMENT_WITH_NAME_AND_ADDRESS": (
                "test country of manufacture statement address [[MANUFACTURED_AT_NAME]] [[MANUFACTURED_AT_ADDRESS_FLAT]] [[COUNTRY_OF_MANUFACTURE]]"
            ),
            "para_PRODUCTS": "test products",
        }

    def test_get_edit_schedule_paragraph_translation_page(self):
        response = self.ilb_admin_client.get(self.url)
        assertContains(response, "CFS Schedule Translation paragraphs")

    def test_edit_schedule_paragraph_translation_page(self):
        response = self.ilb_admin_client.post(self.url, data=self.paragraph_data)
        assert response.status_code == HTTPStatus.FOUND

        self.template.refresh_from_db()
        paragraph = self.template.paragraphs.get(name="SCHEDULE_HEADER")
        assert paragraph.content == "test schedule header"

    def test_get_edit_schedule_paragraph_translation_page_missing_placeholder(self):
        response = self.ilb_admin_client.post(
            self.url, data=self.paragraph_data | {"para_SCHEDULE_INTRODUCTION": "test introduction"}
        )
        assert response.status_code == HTTPStatus.OK

        self.template.refresh_from_db()
        paragraph = self.template.paragraphs.get(name="SCHEDULE_HEADER")
        assert paragraph.content != "test schedule header"

        paragraph = self.template.paragraphs.get(name="SCHEDULE_INTRODUCTION")
        assert paragraph.content != "test introduction"

    def test_get_edit_schedule_paragraph_translation_page_extra_placeholder(self):
        response = self.ilb_admin_client.post(
            self.url,
            data=self.paragraph_data
            | {
                "para_SCHEDULE_INTRODUCTION": "test introduction [[EXPORTER_ADDRESS_FLAT]] [[EXPORTER_NAME]] [[EXTRA]]"
            },
        )
        assert response.status_code == HTTPStatus.OK

        self.template.refresh_from_db()
        paragraph = self.template.paragraphs.get(name="SCHEDULE_HEADER")
        assert paragraph.content != "test schedule header"

        paragraph = self.template.paragraphs.get(name="SCHEDULE_INTRODUCTION")
        assert paragraph.content != "test introduction"


class TestEndorsementUsages(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.endorsement = Template.objects.filter(
            is_active=True,
            endorsement_application_types__isnull=True,
            template_type=Template.ENDORSEMENT,
        ).first()

        self.application_type = ImportApplicationType.objects.filter(
            endorsements__isnull=False, is_active=True
        ).first()
        self.endorsement_count = self.application_type.endorsements.count()

        self.list_url = "/template/endorsement/usages/"
        self.usage_url = f"{self.list_url}{self.application_type.pk}/edit/"

    def test_list_view_admin(self):
        response = self.ilb_admin_client.get(self.list_url)
        assert response.status_code == HTTPStatus.OK

    def test_list_view_importer(self):
        response = self.importer_client.get(self.list_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_list_view_exporter(self):
        response = self.exporter_client.get(self.list_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_view_endorsement_usage(self):
        response = self.ilb_admin_client.get(self.usage_url)
        assert response.status_code == HTTPStatus.OK

    def test_edit_endorsement_usage(self):
        assert self.endorsement not in self.application_type.endorsements.all()
        response = self.ilb_admin_client.post(
            self.usage_url, data={"endorsement": self.endorsement.pk}
        )
        assert response.status_code == HTTPStatus.OK
        self.application_type.refresh_from_db()
        assert self.application_type.endorsements.count() == self.endorsement_count + 1
        assert self.endorsement in self.application_type.endorsements.all()

    def test_edit_endorsement_usage_invalid(self):
        response = self.ilb_admin_client.post(self.usage_url, data={})
        assert response.status_code == HTTPStatus.OK
        self.application_type.refresh_from_db()
        assert self.application_type.endorsements.count() == self.endorsement_count

    def test_remove_endorsement_usage(self):
        endorsement = self.application_type.endorsements.first()
        url = reverse(
            "template-endorsement-usage-link-remove",
            kwargs={"application_type_pk": self.application_type.pk, "link_pk": endorsement.pk},
        )
        response = self.ilb_admin_client.post(url)
        assert response.status_code == HTTPStatus.FOUND
        self.application_type.refresh_from_db()
        assert endorsement not in self.application_type.endorsements.all()
        assert self.application_type.endorsements.count() == self.endorsement_count - 1
