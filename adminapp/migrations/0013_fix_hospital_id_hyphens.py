# Generated migration to fix hospital ID hyphen format

from django.db import migrations


def fix_hospital_id_hyphens(apps, schema_editor):
    """Fix hospital ID format by removing hyphens from references"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Fix appointments with hyphenated hospital IDs
        cursor.execute("""
            UPDATE adminapp_appointment 
            SET hospital_id = REPLACE(hospital_id, '-', '') 
            WHERE hospital_id LIKE '%-%'
            AND REPLACE(hospital_id, '-', '') IN (SELECT id FROM tenants_hospital)
        """)
        
        # Fix doctors with hyphenated hospital IDs
        cursor.execute("""
            UPDATE adminapp_doctor 
            SET hospital_id = REPLACE(hospital_id, '-', '') 
            WHERE hospital_id LIKE '%-%'
            AND REPLACE(hospital_id, '-', '') IN (SELECT id FROM tenants_hospital)
        """)
        
        # Fix categories with hyphenated hospital IDs
        try:
            cursor.execute("""
                UPDATE adminapp_category 
                SET hospital_id = REPLACE(hospital_id, '-', '') 
                WHERE hospital_id LIKE '%-%'
                AND REPLACE(hospital_id, '-', '') IN (SELECT id FROM tenants_hospital)
            """)
        except:
            pass
        
        # Fix availability records with hyphenated hospital IDs
        try:
            cursor.execute("""
                UPDATE adminapp_doctoravailability 
                SET hospital_id = REPLACE(hospital_id, '-', '') 
                WHERE hospital_id LIKE '%-%'
                AND REPLACE(hospital_id, '-', '') IN (SELECT id FROM tenants_hospital)
            """)
        except:
            pass
        
        # Fix review records with hyphenated hospital IDs
        try:
            cursor.execute("""
                UPDATE adminapp_doctorreview 
                SET hospital_id = REPLACE(hospital_id, '-', '') 
                WHERE hospital_id LIKE '%-%'
                AND REPLACE(hospital_id, '-', '') IN (SELECT id FROM tenants_hospital)
            """)
        except:
            pass


def reverse_fix(apps, schema_editor):
    # This is irreversible - we can't restore the original hyphenated format
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('adminapp', '0011_fix_orphaned_references'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fix_hospital_id_hyphens, reverse_fix),
    ]