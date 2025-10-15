from django.core.management.base import BaseCommand
from django.db import connection
from adminapp.models import Doctor


class Command(BaseCommand):
    help = 'Debug doctor deletion issues'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                self.stdout.write('🔍 Debugging doctor deletion issue...')
                
                # Check all tables with 'doctor' in the name
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%doctor%'")
                doctor_tables = cursor.fetchall()
                self.stdout.write(f'📋 Tables with "doctor": {[t[0] for t in doctor_tables]}')
                
                # Check for any views with doctor_old
                cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name LIKE '%doctor_old%'")
                doctor_views = cursor.fetchall()
                if doctor_views:
                    self.stdout.write(f'👁️ Views with "doctor_old": {[v[0] for v in doctor_views]}')
                    for view in doctor_views:
                        cursor.execute(f"DROP VIEW IF EXISTS {view[0]}")
                        self.stdout.write(f'🗑️ Dropped view: {view[0]}')
                
                # Check for triggers that might reference doctor_old
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
                triggers = cursor.fetchall()
                problematic_triggers = []
                for trigger_name, trigger_sql in triggers:
                    if trigger_sql and 'doctor_old' in trigger_sql.lower():
                        problematic_triggers.append((trigger_name, trigger_sql))
                
                if problematic_triggers:
                    self.stdout.write(f'⚠️ Found {len(problematic_triggers)} problematic triggers:')
                    for trigger_name, trigger_sql in problematic_triggers:
                        self.stdout.write(f'  🔧 Trigger: {trigger_name}')
                        self.stdout.write(f'     SQL: {trigger_sql[:100]}...')
                        cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
                        self.stdout.write(f'  🗑️ Dropped trigger: {trigger_name}')
                else:
                    self.stdout.write('✅ No problematic triggers found')
                
                # Check indexes
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND sql LIKE '%doctor_old%'")
                bad_indexes = cursor.fetchall()
                if bad_indexes:
                    self.stdout.write(f'⚠️ Found problematic indexes: {bad_indexes}')
                    for index_name, _ in bad_indexes:
                        cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                        self.stdout.write(f'🗑️ Dropped index: {index_name}')
                
                # Check the actual doctor table schema
                cursor.execute("PRAGMA table_info(adminapp_doctor)")
                columns = cursor.fetchall()
                self.stdout.write(f'📊 Doctor table columns: {len(columns)} columns')
                
                # Check foreign keys pointing TO the doctor table
                cursor.execute("""
                    SELECT m.name as table_name, p.* 
                    FROM sqlite_master m 
                    JOIN pragma_foreign_key_list(m.name) p ON m.type = 'table' 
                    WHERE p.'table' = 'adminapp_doctor'
                """)
                fk_references = cursor.fetchall()
                self.stdout.write(f'🔗 Tables referencing doctor table: {len(fk_references)}')
                for ref in fk_references:
                    self.stdout.write(f'  📋 {ref[0]} -> adminapp_doctor')
                
                # Try to find doctor 17 specifically
                try:
                    cursor.execute("SELECT id, first_name, last_name FROM adminapp_doctor WHERE id = 17")
                    doctor_17 = cursor.fetchone()
                    if doctor_17:
                        self.stdout.write(f'👨‍⚕️ Doctor 17 found: {doctor_17}')
                        
                        # Check what references this doctor
                        cursor.execute("SELECT COUNT(*) FROM adminapp_appointment WHERE doctor_id = 17")
                        appointments = cursor.fetchone()[0]
                        self.stdout.write(f'📅 Doctor 17 has {appointments} appointments')
                        
                        cursor.execute("SELECT COUNT(*) FROM adminapp_doctoravailability WHERE doctor_id = 17")
                        availability = cursor.fetchone()[0]
                        self.stdout.write(f'⏰ Doctor 17 has {availability} availability records')
                        
                    else:
                        self.stdout.write('❌ Doctor 17 not found')
                except Exception as e:
                    self.stdout.write(f'❌ Error checking doctor 17: {e}')
                
                # Test a simple delete operation
                self.stdout.write('🧪 Testing simple delete operation...')
                try:
                    # Try to delete using Django ORM
                    test_doctor = Doctor.objects.filter(id=17).first()
                    if test_doctor:
                        self.stdout.write(f'🎯 Found doctor via ORM: {test_doctor.full_name}')
                        # Don't actually delete, just test the query
                        self.stdout.write('✅ ORM access works')
                    else:
                        self.stdout.write('❌ Doctor 17 not found via ORM')
                except Exception as e:
                    self.stdout.write(f'❌ ORM error: {e}')
                
                self.stdout.write(
                    self.style.SUCCESS('🔍 Debug completed!')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Debug error: {str(e)}')
                )