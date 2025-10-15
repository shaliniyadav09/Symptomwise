from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Force fix doctor table issues by recreating clean structure'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                self.stdout.write('🔧 Force fixing doctor table issues...')
                
                # Step 1: Disable foreign keys temporarily
                cursor.execute("PRAGMA foreign_keys = OFF")
                self.stdout.write('🔓 Disabled foreign keys')
                
                # Step 2: Get current doctor table structure
                cursor.execute("PRAGMA table_info(adminapp_doctor)")
                columns = cursor.fetchall()
                self.stdout.write(f'📋 Current doctor table has {len(columns)} columns')
                
                # Step 3: Check for any problematic objects
                cursor.execute("SELECT name, type, sql FROM sqlite_master WHERE sql LIKE '%doctor_old%'")
                problematic_objects = cursor.fetchall()
                
                if problematic_objects:
                    self.stdout.write(f'⚠️ Found {len(problematic_objects)} problematic objects:')
                    for name, obj_type, sql in problematic_objects:
                        self.stdout.write(f'  🗑️ Dropping {obj_type}: {name}')
                        if obj_type == 'trigger':
                            cursor.execute(f"DROP TRIGGER IF EXISTS {name}")
                        elif obj_type == 'view':
                            cursor.execute(f"DROP VIEW IF EXISTS {name}")
                        elif obj_type == 'index':
                            cursor.execute(f"DROP INDEX IF EXISTS {name}")
                else:
                    self.stdout.write('✅ No problematic objects found')
                
                # Step 4: Check all triggers on doctor table
                cursor.execute("""
                    SELECT name, sql FROM sqlite_master 
                    WHERE type='trigger' AND tbl_name='adminapp_doctor'
                """)
                doctor_triggers = cursor.fetchall()
                
                if doctor_triggers:
                    self.stdout.write(f'🔍 Found {len(doctor_triggers)} triggers on doctor table:')
                    for trigger_name, trigger_sql in doctor_triggers:
                        self.stdout.write(f'  📋 {trigger_name}')
                        if 'doctor_old' in trigger_sql.lower():
                            self.stdout.write(f'    ⚠️ Contains doctor_old reference - DROPPING')
                            cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name}")
                        else:
                            self.stdout.write(f'    ✅ Clean trigger')
                
                # Step 5: Check for any views that might reference doctor_old
                cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='view'")
                all_views = cursor.fetchall()
                for view_name, view_sql in all_views:
                    if view_sql and 'doctor_old' in view_sql.lower():
                        self.stdout.write(f'🗑️ Dropping problematic view: {view_name}')
                        cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
                
                # Step 6: Vacuum the database to clean up
                self.stdout.write('🧹 Cleaning up database...')
                cursor.execute("VACUUM")
                
                # Step 7: Re-enable foreign keys
                cursor.execute("PRAGMA foreign_keys = ON")
                self.stdout.write('🔒 Re-enabled foreign keys')
                
                # Step 8: Test doctor deletion capability
                self.stdout.write('🧪 Testing doctor deletion...')
                cursor.execute("SELECT id, first_name, last_name FROM adminapp_doctor LIMIT 1")
                test_doctor = cursor.fetchone()
                
                if test_doctor:
                    doctor_id = test_doctor[0]
                    self.stdout.write(f'🎯 Test doctor found: ID {doctor_id}')
                    
                    # Test the deletion query without actually deleting
                    cursor.execute("EXPLAIN QUERY PLAN DELETE FROM adminapp_doctor WHERE id = ?", [doctor_id])
                    query_plan = cursor.fetchall()
                    self.stdout.write(f'📊 Deletion query plan: {len(query_plan)} steps')
                    
                    for step in query_plan:
                        if 'doctor_old' in str(step).lower():
                            self.stdout.write(f'❌ Query plan still references doctor_old: {step}')
                        else:
                            self.stdout.write(f'✅ Clean query step: {step}')
                else:
                    self.stdout.write('ℹ️ No doctors found for testing')
                
                # Step 9: Check database integrity
                cursor.execute("PRAGMA integrity_check")
                integrity = cursor.fetchone()
                if integrity[0] == 'ok':
                    self.stdout.write('✅ Database integrity check passed')
                else:
                    self.stdout.write(f'⚠️ Database integrity issues: {integrity[0]}')
                
                self.stdout.write(
                    self.style.SUCCESS('🎉 Force fix completed! Try deleting the doctor now.')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Force fix error: {str(e)}')
                )
                # Try to re-enable foreign keys even if there was an error
                try:
                    cursor.execute("PRAGMA foreign_keys = ON")
                except:
                    pass