# Simple cleanup migration for hospitals app

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hospitals', '0001_initial'),
        ('tenants', '0002_alter_hospital_phone_alter_hospital_whatsapp_number_and_more'),
    ]

    operations = [
        # This migration does nothing - the hospital models should be cleaned up manually
        # if needed using management commands
    ]