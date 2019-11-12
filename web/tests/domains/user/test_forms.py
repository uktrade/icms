# from django.test import TestCase
# from web.domains.constabulary.forms import (ConstabularyForm,
#                                             ConstabulariesFilter)
# from web.domains.constabulary.models import Constabulary
#
# from .factory import UserFactory
#
#
# class ConstabulariesFilterTest(TestCase):
#     def setUp(self):
#         UserFactory(name='Test Constabulary',
#                             region=Constabulary.EAST_MIDLANDS,
#                             email='test_constabulary@example.com',
#                             is_active=False)
#         UserFactory(name='Big London Constabulary',
#                             region=Constabulary.EASTERN,
#                             email='london_constabulary@example.com',
#                             is_active=True)
#         UserFactory(name='That Constabulary',
#                             region=Constabulary.EASTERN,
#                             email='that_constabulary@example.com',
#                             is_active=True)
#
#     def run_filter(self, data=None):
#         return ConstabulariesFilter(data=data).qs
#
#     def test_name_filter(self):
#         results = self.run_filter({'name': 'constab'})
#         self.assertEqual(results.count(), 2)
#
#     def test_archived_filter(self):
#         results = self.run_filter({'archived': True})
#         self.assertEqual(results.count(), 1)
#         self.assertEqual(results.first().name, 'Test Constabulary')
#
#     def test_region_filter(self):
#         results = self.run_filter({'region': Constabulary.EASTERN})
#         self.assertEqual(results.count(), 2)
#
#     def test_email_filter(self):
#         results = self.run_filter({'email': '@example.com'})
#         self.assertEqual(results.count(), 2)
#
#     def test_filter_order(self):
#         results = self.run_filter({'email': 'example'})
#         self.assertEqual(results.count(), 2)
#         first = results.first()
#         last = results.last()
#         self.assertEqual(first.name, 'Big London Constabulary')
#         self.assertEqual(last.name, 'That Constabulary')
#
#
# class ProductLegislationFormTest(TestCase):
#     def test_form_valid(self):
#         form = ConstabularyForm(
#             data={
#                 'name': 'Testing',
#                 'region': Constabulary.WEST_MIDLANDS,
#                 'email': 'test@example.com'
#             })
#         self.assertTrue(form.is_valid())
#
#     def test_form_invalid(self):
#         form = ConstabularyForm(
#             data={
#                 'name': 'Test',
#                 'region': Constabulary.ISLE_OF_MAN,
#                 'email': 'invalidmail'
#             })
#         self.assertFalse(form.is_valid())
#
#     def test_invalid_form_message(self):
#         form = ConstabularyForm(
#             data={
#                 'name': 'Test',
#                 'region': Constabulary.ISLE_OF_MAN,
#                 'email': 'invalidmail'
#             })
#         self.assertEqual(len(form.errors), 1)
#         message = form.errors['email'][0]
#         self.assertEqual(message, 'Enter a valid email address.')
