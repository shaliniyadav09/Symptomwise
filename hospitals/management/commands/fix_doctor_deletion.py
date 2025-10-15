from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix doctor deletion issues by checking and cleaning database'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                self.stdout.write('Checking database tables...')
                
                # Check if the correct table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='adminapp_doctor'")
                if cursor.fetchone():
                    self.stdout.write('  ✅ adminapp_doctor table exists')
                else:
                    self.stdout.write('  ❌ adminapp_doctor table missing')
                
                # Check for any old table references
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%doctor_old%'")
                old_tables = cursor.fetchall()
                if old_tables:
                    self.stdout.write(f'  ⚠️  Found old tables: {old_tables}')
                    for table in old_tables:
                        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
                        self.stdout.write(f'  🗑️  Dropped old table: {table[0]}')
                else:
                    self.stdout.write('  ✅ No old doctor tables found')
                
                # Check foreign key constraints
                cursor.execute("PRAGMA foreign_key_list(adminapp_appointment)")
                fk_constraints = cursor.fetchall()
                
                doctor_fk_found = False
                for constraint in fk_constraints:
                    if 'doctor' in str(constraint):
                        doctor_fk_found = True
                        self.stdout.write(f'  📋 Doctor FK constraint: {constraint}')
                
                if not doctor_fk_found:
                    self.stdout.write('  ⚠️  No doctor foreign key constraints found in appointments')
                
                # Check if there are any problematic triggers
                cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND sql LIKE '%doctor_old%'")
                bad_triggers = cursor.fetchall()
                if bad_triggers:
                    self.stdout.write(f'  ⚠️  Found problematic triggers: {bad_triggers}')
                    for trigger in bad_triggers:
                        cursor.execute(f"DROP TRIGGER IF EXISTS {trigger[0]}")
                        self.stdout.write(f'  🗑️  Dropped trigger: {trigger[0]}')
                else:
                    self.stdout.write('  ✅ No problematic triggers found')
                
                # Test doctor deletion capability
                cursor.execute("SELECT COUNT(*) FROM adminapp_doctor")
                doctor_count = cursor.fetchone()[0]
                self.stdout.write(f'  📊 Total doctors in database: {doctor_count}')
                
                # Check for orphaned records
                cursor.execute("""
                    SELECT COUNT(*) FROM adminapp_appointment 
                    WHERE doctor_id IS NOT NULL 
                    AND doctor_id NOT IN (SELECT id FROM adminapp_doctor)
                """)
                orphaned_appointments = cursor.fetchone()[0]
                
                if orphaned_appointments > 0:
                    self.stdout.write(f'  ⚠️  Found {orphaned_appointments} orphaned appointments')
                    cursor.execute("""
                        UPDATE adminapp_appointment 
                        SET doctor_id = NULL 
                        WHERE doctor_id IS NOT NULL 
                        AND doctor_id NOT IN (SELECT id FROM adminapp_doctor)
                    """)
                    self.stdout.write(f'  🔧 Fixed {orphaned_appointments} orphaned appointments')
                else:
                    self.stdout.write('  ✅ No orphaned appointments found')
                
                # Check availability records
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM adminapp_doctoravailability 
                        WHERE doctor_id NOT IN (SELECT id FROM adminapp_doctor)
                    """)
                    orphaned_availability = cursor.fetchone()[0]
                    
                    if orphaned_availability > 0:
                        self.stdout.write(f'  ⚠️  Found {orphaned_availability} orphaned availability records')
                        cursor.execute("""
                            DELETE FROM adminapp_doctoravailability 
                            WHERE doctor_id NOT IN (SELECT id FROM adminapp_doctor)
                        """)
                        self.stdout.write(f'  🔧 Cleaned {orphaned_availability} orphaned availability records')
                    else:
                        self.stdout.write('  ✅ No orphaned availability records found')
                except Exception as e:
                    self.stdout.write(f'  ⚠️  Could not check availability: {str(e)}')
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Database cleanup completed successfully!')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error during cleanup: {str(e)}')
                )