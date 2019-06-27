from django.db import migrations
from web.models import User


def create_default_user(apps, schema_editor):
    user = User(username='admin', is_superuser=True, title='Mr',
                first_name='Admin', last_name='Gov')
    user.set_password('admin')    # will force to reset at login
    user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0030_calibres_data'),
    ]

    operations = [
        migrations.RunPython(create_default_user),
    ]
