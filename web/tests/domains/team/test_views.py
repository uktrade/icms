from web.tests.auth import AuthTestCase
from web.tests.domains.user.factory import UserFactory

from .factory import RoleFactory, TeamFactory

LOGIN_URL = "/"


class TeamListViewTest(AuthTestCase):
    url = "/teams/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def create_team_role(self, role_name):
        """
            Creates a team with a role of given name
        """
        team = TeamFactory(name="Test Team")
        role = RoleFactory(name=role_name, team=team)
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
        self.create_team_role("Team:Resource Co-ordinator").user_set.add(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_team_coordinator_access(self):
        self.login()
        self.create_team_role("Team:Team Coordinator").user_set.add(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_only_coordinated_teams_displayed(self):
        self.login()
        self.create_team_role("Team:Resource Co-ordinator").user_set.add(self.user)
        TeamFactory(name="Some team")
        TeamFactory(name="Another team")
        response = self.client.get(self.url)
        teams = response.context_data["object_list"]
        self.assertEqual(len(teams), 1)
        self.assertEqual(teams[0].name, "Test Team")

    def test_superuser_sees_all_teams(self):
        self.login()
        self.user.is_superuser = True
        self.user.save()
        TeamFactory(name="Some team")
        TeamFactory(name="Another team")
        TeamFactory(name="Yet Another team")
        response = self.client.get(self.url)
        teams = response.context_data["object_list"]
        self.assertEqual(len(teams), 3)
        self.assertEqual(teams[0].name, "Another team")
        self.assertEqual(teams[1].name, "Some team")
        self.assertEqual(teams[2].name, "Yet Another team")

    def test_page_title(self):
        self.login()
        self.create_team_role("Team:Team Coordinators").user_set.add(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data["page_title"], "Search Teams")


class TeamEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.team = TeamFactory(name="Test Team")
        self.role = RoleFactory(name="Team:Resource Co-ordinator", team=self.team)
        self.url = f"/teams/{self.team.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def login_as_coordinator(self):
        self.login()
        self.role.user_set.add(self.user)  # Assign coordinator role

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_coordinator_access(self):
        self.login_as_coordinator()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_of_members(self):
        self.login_as_coordinator()
        user = UserFactory(username="Hello")
        self.team.members.add(user)
        response = self.client.get(self.url)
        members = response.context_data["members"]
        self.assertTrue(len(members), 1)
        self.assertTrue(user in members)

    def test_list_of_roles(self):
        self.login_as_coordinator()
        role = RoleFactory(name="Test Team:Test Role", team=self.team)
        response = self.client.get(self.url)
        roles = response.context_data["roles"]
        self.assertTrue(len(roles), 2)
        self.assertTrue(role in roles)

    def test_role_members(self):
        self.login_as_coordinator()
        user = UserFactory()
        self.role.user_set.add(user)
        response = self.client.get(self.url)
        role_members = response.context_data["role_members"]
        member_ids = role_members[str(self.role.id)]
        self.assertTrue(len(member_ids), 2)
        self.assertTrue(str(self.user.id) in member_ids)
        self.assertTrue(str(user.id) in member_ids)

    def test_forbidden_post_access(self):
        self.login()
        response = self.client.post(self.url, {"action": "add_member"})
        self.assertEqual(response.status_code, 403)

    def test_coordinator_post_access(self):
        self.login_as_coordinator()
        response = self.client.post(self.url, {"action": "add_member"})
        self.assertEqual(response.status_code, 200)

    def test_add_member_renders_search_people(self):
        self.login_as_coordinator()
        response = self.client.post(self.url, {"action": "add_member"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data["page_title"], "Search People")

    def test_add_member_saves_form_changes_to_session(self):
        self.login_as_coordinator()
        UserFactory()
        UserFactory()
        self.client.post(
            self.url,
            {"action": "add_member", "name": "Super Team", "description": "Super team description"},
        )
        session = self.client.session
        form = session[f"team:{self.team.id}"]["form"]
        self.assertEqual(form["name"], "Super Team")
        self.assertEqual(form["description"], "Super team description")

    def test_add_member_saves_member_changes_to_session(self):
        self.login_as_coordinator()
        user = UserFactory()
        user2 = UserFactory()
        self.client.post(self.url, {"action": "add_member", "members": [user.id, user2.id]})
        session = self.client.session
        members = session[f"team:{self.team.id}"]["members"]
        self.assertEqual(len(members), 2)
        self.assertTrue(str(user.id) in members)
        self.assertTrue(str(user2.id) in members)

    def test_add_member_saves_role_changes_to_session(self):
        self.login_as_coordinator()
        user = UserFactory()
        user2 = UserFactory()
        role = RoleFactory(name="Super user", team=self.team)
        self.client.post(
            self.url, {"action": "add_member", f"role_members_{role.id}": [user.id, user2.id]}
        )
        session = self.client.session
        role_members = session[f"team:{self.team.id}"]["role_members"][str(role.id)]
        self.assertEqual(len(role_members), 2)
        self.assertTrue(str(user.id) in role_members)
        self.assertTrue(str(user2.id) in role_members)

    def test_add_people(self):
        self.login_as_coordinator()
        session = self.client.session
        user = UserFactory()
        user2 = UserFactory()
        session[f"team:{self.team.id}"] = {"members": []}
        session.save()
        response = self.client.post(
            self.url, {"action": "add_people", "selected_items": [user.id, user2.id]}
        )
        members = response.context_data["members"]
        self.assertEqual(len(members), 2)
        self.assertTrue(user in members)
        self.assertTrue(user2 in members)

    def test_remove_member_removes_roles(self):
        self.login_as_coordinator()
        user = UserFactory()
        role = RoleFactory(name="Some Team:Some Role", team=self.team)
        role2 = RoleFactory(name="Some Team:Another Role", team=self.team)
        role.user_set.add(user)
        role2.user_set.add(user)
        self.team.members.add(user)
        self.client.post(self.url, {"action": "save", "name": "Test Team", "members": []})
        self.assertTrue(user not in role.user_set.all())
        self.assertTrue(user not in role2.user_set.all())
