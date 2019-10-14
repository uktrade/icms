from django.test import TestCase


class UsersTestMixin(TestCase):
    fixtures = ['web/fixtures/web/users.json']

    def setUp
