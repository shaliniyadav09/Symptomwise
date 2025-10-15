# Generated migration to fix orphaned doctor references

from django.db import migrations


def fix_orphaned_references(apps, schema_editor):
    """Fix orphaned doctor references in related tables"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Fix orphaned appointments - set doctor_id to NULL
        cursor.execute("""
            UPDATE adminapp_appointment 
            SET doctor_id = NULL 
            WHERE doctor_id IS NOT NULL 
            AND doctor_id NOT IN (SELECT id FROM adminapp_doctor)
        """)
        
        # Delete orphaned availability records
        cursor.execute("""
            DELETE FROM adminapp_doctoravailability 
            WHERE doctor_id NOT IN (SELECT id FROM adminapp_doctor)
        """)
        
        # Delete orphaned review records
        cursor.execute("""
            DELETE FROM adminapp_doctorreview 
            WHERE doctor_id NOT IN (SELECT id FROM adminapp_doctor)
        """)


def reverse_fix(apps, schema_editor):
    # This is irreversible - we can't restore deleted orphaned records
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0010_fix_appointment_foreign_key'),
    ]

    operations = [
        migrations.RunPython(fix_orphaned_references, reverse_fix),
    ]