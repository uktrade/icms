from django.test import TestCase
from web.domains.user.models import User


class UserTest(TestCase):
    def create_user(
            self,
            title='Mr',
            preffered_first_name='Jon',
            middle_initials='G',
            organisation='House of Jon',
            department='Sales',
            job_title='CEO',
            location_at_address='Floor 18',
            work_address='Windsor House, 50 Victoria Street, London, SW1H 0TL',
            date_of_birth='2000-01-01',
            security_question='Are ghosts real',
            security_answer='retroactive rationalisation',
            register_complete=True,
            share_contact_details=True,
            account_status=User.NEW,
            account_status_date='2019-01-01',
            password_disposition=User.FULL
    ):
        return User.objects.create(title=title,
                                   preffered_first_name=preffered_first_name,
                                   middle_initials=middle_initials,
                                   organisation=organisation,
                                   department=department,
                                   job_title=job_title,
                                   location_at_address=location_at_address,
                                   work_address=work_address,
                                   date_of_birth=date_of_birth,
                                   security_question=security_question,
                                   security_answer=security_answer,
                                   register_complete=register_complete,
                                   share_contact_details=share_contact_details,
                                   account_status=account_status,
                                   account_status_date=account_status_date,
                                   password_disposition=password_disposition)

    def test_create_user(self):
        user = self.create_user()
        self.assertTrue(isinstance(user, User))
        # self.assertEqual(constabulary.name, 'Test Constabulary')
        # self.assertEqual(constabulary.email, 'test_constabulary@test.com')
        # self.assertEqual(constabulary.region, Constabulary.EAST_MIDLANDS)
        # self.assertTrue(constabulary.is_active)

    # def test_archive_constabulary(self):
    #     constabulary = self.create_constabulary()
    #     constabulary.archive()
    #     self.assertFalse(constabulary.is_active)
    #
    # def test_unarchive_constabulary(self):
    #     constabulary = self.create_constabulary()
    #     constabulary.unarchive()
    #     self.assertTrue(constabulary.is_active)
    #
    # def test_region_verbose(self):
    #     constabulary = self.create_constabulary()
    #     self.assertEqual(constabulary.region_verbose, 'East Midlands')
    #
    # def test_string_representation(self):
    #     constabulary = self.create_constabulary()
    #     self.assertEqual(constabulary.__str__(),
    #                      f'Constabulary ({constabulary.name})')
