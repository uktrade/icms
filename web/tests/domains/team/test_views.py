from web.tests.auth import AuthTestCase

from .factory import TeamFactory, RoleFactory

LOGIN_URL = '/'


class TeamListViewTest(AuthTestCase):
    url = '/teams/'
    redirect_url = f'{LOGIN_URL}?next={url}'

    def create_team_role(self, role_name):
        """
            Creates a team with a role of given name
        """
        team = TeamFactory(name='Test Team')
        role = RoleFactory(name=role_name, team=team)
        team.roles.add(role)
        return role

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_superuser_access(self):
        self.user.is_superuser = True
        self.user.save()
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_resource_coordinator_acces(self):
        self.login()
        self.create_team_role('Team:Resource Co-ordinator').user_set.add(
            self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_team_coordinator_access(self):
        self.login()
        self.create_team_role('Team:Team Coordinator').user_set.add(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_only_coordinated_teams_displayed(self):
        self.login()
        self.create_team_role('Team:Resource Co-ordinator').user_set.add(
            self.user)
        TeamFactory(name='Some team')
        TeamFactory(name='Another team')
        response = self.client.get(self.url)
        teams = response.context_data['object_list']
        self.assertEqual(len(teams), 1)
        self.assertEqual(teams[0].name, 'Test Team')

    def test_superuser_sees_all_teams(self):
        self.login()
        self.user.is_superuser = True
        self.user.save()
        TeamFactory(name='Some team')
        TeamFactory(name='Another team')
        TeamFactory(name='Yet Another team')
        response = self.client.get(self.url)
        teams = response.context_data['object_list']
        self.assertEqual(len(teams), 3)
        self.assertEqual(teams[0].name, 'Another team')
        self.assertEqual(teams[1].name, 'Some team')
        self.assertEqual(teams[2].name, 'Yet Another team')

    def test_page_title(self):
        self.login()
        self.create_team_role('Team:Team Coordinators').user_set.add(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'], 'Search Teams')


class TeamEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.team = TeamFactory(name='Test Team')
        self.role = RoleFactory(name='Team:Resource Co-ordinator')
        self.team.roles.add(self.role)
        self.url = f'/teams/{self.team.id}/edit/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_coordinator_access(self):
        self.login()
        self.role.user_set.add(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
