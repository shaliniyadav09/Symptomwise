# Manual database fix migration - run management command first

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0013_fix_hospital_id_hyphens'),
    ]

    operations = [
        # This migration does nothing - the database should be fixed manually
        # using the management command: python manage.py fix_database_completely
    ]