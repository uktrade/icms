from web.tests.auth import AuthTestCase

from .factory import CountryFactory, CountryGroupFactory

LOGIN_URL = '/'
PERMISSIONS = ['COUNTRY_SUPER_USERS:COUNTRY_SET_SUPER_USER:COUNTRY_MANAGE']


class CountryListViewTest(AuthTestCase):
    url = '/country/'
    redirect_url = f'{LOGIN_URL}?next={url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Editing All Countries')

    def test_page_results(self):
        for i in range(3):
            CountryFactory()
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        results = response.context_data['object_list']
        self.assertEqual(len(results), 3)


class CountryEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.country = CountryFactory(name='Astoria')
        self.url = f'/country/{self.country.id}/edit/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         "Editing Country (Astoria)")


class CountryCreateViewTest(AuthTestCase):
    url = '/country/new/'
    redirect_url = f'{LOGIN_URL}?next={url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'], 'New Country')


class CountryGroupDefaultView(AuthTestCase):
    def setUp(self):
        super().setUp()
        CountryGroupFactory(name='Asian Countries')
        CountryGroupFactory(name='American Countries')
        self.url = f'/country/groups/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Viewing Country Group (American Countries)')


class CountryGroupView(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.group = CountryGroupFactory(name='European Countries')
        self.url = f'/country/groups/{self.group.id}/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Viewing Country Group (European Countries)')


class CountryGroupEditView(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.group = CountryGroupFactory(name='African Countries')
        self.url = f'/country/groups/{self.group.id}/edit/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'

    def setupCountries(self):
        self.benin = CountryFactory(name='Benin', is_active=True)
        self.kenya = CountryFactory(name='Kenya', is_active=True)
        self.ethiopia = CountryFactory(name='Ethiopia', is_active=True)
        self.group.countries.set([self.kenya, self.benin])

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Editing Country Group (African Countries)')

    def test_group_countries(self):
        self.setupCountries()
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        countries = response.context_data['countries']
        self.assertEqual(len(countries),2)
        self.assertEqual(countries[0].name, 'Benin')
        self.assertEqual(countries[1].name, 'Kenya')

    def test_post_action_anonymous_access(self):
        response = self.client.post(self.url, {'action': 'add_country'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_post_action_forbidden_access(self):
        self.login()
        response = self.client.post(self.url, {'action': 'add_country'})
        self.assertEqual(response.status_code, 403)

    def test_add_country_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(self.url, {'action': 'add_country'})
        self.assertEqual(response.context_data['page_title'], 'Country Search')

    def test_add_country_selected_countries(self):
        self.setupCountries()
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(self.url, {
            'action': 'add_country',
            'countries': [self.benin.id, self.kenya.id]
        })
        context = response.context_data
        self.assertEqual(len(context['selected_countries']), 2)
        self.assertEqual(context['selected_countries'][0].name, 'Benin')
        self.assertEqual(context['selected_countries'][1].name, 'Kenya')

    def test_accept_countries(self):
        self.setupCountries()
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(
            self.url, {
                'action':
                'accept_countries',
                'country-selection':
                [self.benin.id, self.kenya.id, self.ethiopia.id]
            })
        countries = response.context_data['countries']
        self.assertEqual(len(countries), 3)
        self.assertEqual(countries[0].name, 'Benin')
        self.assertEqual(countries[1].name, 'Ethiopia')
        self.assertEqual(countries[2].name, 'Kenya')


#  class MailshotCreateViewTest(AuthTestCase):
#      url = '/mailshot/new/'
#      redirect_url = f'{LOGIN_URL}?next={url}'
#
#      def setUp(self):
#          super().setUp()
#          # Create publish mailshot template for testing
#          TemplateFactory(
#              template_code='PUBLISH_MAILSHOT',
#              template_title='New Mailshot',
#              template_content='Template Content')  # Create mailshot template
#
#      def test_anonymous_access_redirects(self):
#          response = self.client.get(self.url)
#          self.assertEqual(response.status_code, 302)
#          self.assertRedirects(response, self.redirect_url)
#
#      def test_forbidden_access(self):
#          self.login()
#          response = self.client.get(self.url)
#          self.assertEqual(response.status_code, 403)
#
#      def test_authorized_access_redirects(self):
#          self.login_with_permissions(PERMISSIONS)
#          response = self.client.get(self.url)
#          mailshot = Mailshot.objects.first()
#          self.assertEqual(response.status_code, 302)
#          self.assertRedirects(response, f'/mailshot/{mailshot.id}/edit/')
#
#      def test_create_as_draft(self):
#          self.login_with_permissions(PERMISSIONS)
#          self.client.get(self.url)
#          mailshot = Mailshot.objects.first()
#          self.assertEqual(mailshot.status, Mailshot.DRAFT)

#  class MailshotRetractViewTest(AuthTestCase):
#      def setUp(self):
#          super().setUp()
#          TemplateFactory(template_code='RETRACT_MAILSHOT',
#                          template_title='Retract Mailshot',
#                          template_content='Template Content'
#                          )  # Create retraction mail template
#          self.mailshot = MailshotFactory(
#              status=Mailshot.PUBLISHED)  # Create a mailshot
#          self.mailshot.save()
#          self.url = f'/mailshot/{self.mailshot.id}/retract/'
#          self.redirect_url = f'{LOGIN_URL}?next={self.url}'
#
#      def test_anonymous_access_redirects(self):
#          response = self.client.get(self.url)
#          self.assertEqual(response.status_code, 302)
#          self.assertRedirects(response, self.redirect_url)
#
#      def test_forbidden_access(self):
#          self.login()
#          response = self.client.get(self.url)
#          self.assertEqual(response.status_code, 403)
#
#      def test_authorized_access(self):
#          self.login_with_permissions(PERMISSIONS)
#          response = self.client.get(self.url)
#          self.assertEqual(response.status_code, 200)
#
#      def test_page_title(self):
#          self.login_with_permissions(PERMISSIONS)
#          response = self.client.get(self.url)
#          self.assertEqual(response.context_data['page_title'],
#                           f"Retract {self.mailshot}")
#
#
#  class MailshotDetailViewTest(AuthTestCase):
#      def setUp(self):
#          super().setUp()
#          self.mailshot = MailshotFactory()  # Create a mailshot
#          self.mailshot.save()
#          self.url = f'/mailshot/{self.mailshot.id}/'
#          self.redirect_url = f'{LOGIN_URL}?next={self.url}'
#
#      def test_anonymous_access_redirects(self):
#          response = self.client.get(self.url)
#          self.assertEqual(response.status_code, 302)
#          self.assertRedirects(response, self.redirect_url)
#
#      def test_forbidden_access(self):
#          self.login()
#          response = self.client.get(self.url)
#          self.assertEqual(response.status_code, 403)
#
#      def test_authorized_access(self):
#          self.login_with_permissions(PERMISSIONS)
#          response = self.client.get(self.url)
#          self.assertEqual(response.status_code, 200)
#
#      def test_page_title(self):
#          self.login_with_permissions(PERMISSIONS)
#          response = self.client.get(self.url)
#          self.assertEqual(response.context_data['page_title'],
#                           f"Viewing {self.mailshot}")
