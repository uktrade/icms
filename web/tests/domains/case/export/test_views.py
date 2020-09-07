from web.domains.country.models import Country
from web.tests.auth.auth import AuthTestCase
from web.tests.domains.case.export.factories import CertificateOfManufactureApplicationFactory


class TestFlow(AuthTestCase):
    def test_flow(self):
        """Assert flow uses process and update tasks."""
        process = CertificateOfManufactureApplicationFactory.create(status="IN_PROGRESS")
        process.tasks.create(is_active=True, task_type="prepare")

        self.login_with_permissions(["IMP_CERT_EDIT_APPLICATION"])

        # fill the form about application export
        url_start = f"/export/com/{process.pk}/edit/"
        url_agree = f"/export/com/{process.pk}/submit/"

        response = self.client.post(
            url_start,
            data={
                "contact": self.user.pk,
                "countries": Country.objects.last().pk,
                "is_pesticide_on_free_sale_uk": "false",
                "is_manufacturer": "true",
                "product_name": "new product export",
                "chemical_name": "some checmical name",
                "manufacturing_process": "squeeze a few drops",
            },
        )

        # when form is submitted successfuly go to declaration of truth
        self.assertRedirects(response, url_agree)

        # process and task haven't changed
        process.refresh_from_db()
        self.assertEqual(process.status, "IN_PROGRESS")
        self.assertEqual(process.tasks.count(), 1)
        task = process.tasks.get()
        self.assertEqual(task.task_type, "prepare")
        self.assertEqual(task.is_active, True)

        # declaration of truth
        url = f"/export/com/{process.pk}/submit/"
        response = self.client.post(url, data={"confirmation": "I AGREE"})
        self.assertRedirects(response, "/home/")

        process.refresh_from_db()
        self.assertEqual(process.status, "SUBMITTED")

        # a new task has been created
        self.assertEqual(process.tasks.count(), 2)

        # previous task is not active anymore
        prepare_task = process.tasks.get(task_type="prepare")
        self.assertEqual(prepare_task.is_active, False)
        process_task = process.tasks.get(task_type="process")
        self.assertEqual(process_task.is_active, True)


class TestEditComAuth(AuthTestCase):
    url = "/export/com/42/edit/"
    redirect_url = "/?next=/export/com/42/edit/"

    def test_anonymous_access_redirects(self):
        """Assert page is login protected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        """Assert a logged-in user requires permissions."""
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_required_permissions(self):
        """Assert permission is required to access the page."""
        self.login_with_permissions(["IMP_CERT_EDIT_APPLICATION"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class TestEditCom(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.process = CertificateOfManufactureApplicationFactory.create()
        self.url = f"/export/com/{self.process.pk}/edit/"
        self.redirect_url = f"/?next={self.url}"

    def test_post(self):
        """When submitting a successful application user is redirected to a success url."""
        self.process.tasks.create(is_active=True, task_type="prepare")
        self.login_with_permissions(["IMP_CERT_EDIT_APPLICATION"])
        response = self.client.post(
            self.url,
            data={
                "contact": self.user.pk,
                "countries": [Country.objects.last().pk],
                "is_pesticide_on_free_sale_uk": "false",
                "is_manufacturer": "true",
                "product_name": "new product export",
                "chemical_name": "some checmical name",
                "manufacturing_process": "squeeze a few drops",
            },
        )
        self.assertRedirects(response, f"/export/com/{self.process.pk}/submit/")

    def test_no_task(self):
        """Assert an application/flow requires an active task."""
        self.login_with_permissions(["IMP_CERT_EDIT_APPLICATION"])
        with self.assertRaises(Exception, msg="Expected one active task, got 0"):
            self.client.get(self.url)


class TestSubmitComAuth(AuthTestCase):
    url = "/export/com/42/submit/"
    redirect_url = "/?next=/export/com/42/submit/"

    def test_anonymous_access_redirects(self):
        """Assert page is login protected."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        """Assert a logged-in user requires permissions."""
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_required_permissions(self):
        """Assert permission is required to access the page."""
        self.login_with_permissions(["IMP_CERT_EDIT_APPLICATION"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


class TestSubmitCom(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.process = CertificateOfManufactureApplicationFactory.create()
        self.url = f"/export/com/{self.process.pk}/submit/"
        self.redirect_url = f"/?next={self.url}"

    def test_post(self):
        """When submitting a successful application user is redirected to a success url."""
        self.process.tasks.create(is_active=True, task_type="prepare")
        self.login_with_permissions(["IMP_CERT_EDIT_APPLICATION"])
        response = self.client.post(self.url, data={"confirmation": "I AGREE"})
        self.assertRedirects(response, "/home/")

    def test_no_task(self):
        """Assert an application/flow requires an active task."""
        self.login_with_permissions(["IMP_CERT_EDIT_APPLICATION"])
        with self.assertRaises(Exception, msg="Expected one active task, got 0"):
            self.client.get(self.url)
