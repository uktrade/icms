# Generated by Django 4.2.14 on 2024-08-29 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("web", "0032_dfl_sanctions_sil_goods_store_applicant_original"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="show_welcome_message",
            field=models.BooleanField(default=True),
        ),
    ]