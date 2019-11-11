from django.db import migrations
from web.models import User


def create_default_user(apps, schema_editor):
    # will force to reset password at login
    user = User(
        id=-1,
        username='admin',
        is_superuser=True,
        is_staff=False,
        title='Dr.',
        first_name='Admin',
        last_name='Gov',
        security_question='Are you the admin?',
        security_answer='Maybe',
        password=
        'pbkdf2_sha256$150000$A9tWmv8WAOKU$fDGeH1uYJP4QvT8ogLnvYmxOBjhyH6SuJoNbLosr4L0=',
        unsuccessful_login_attempts=0,
        password_disposition=User.TEMPORARY
    )  # NOQA
    user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0076_merge_20191111_1607'),
    ]

    operations = [
        migrations.RunPython(create_default_user),
    ]
