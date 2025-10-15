from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Completely fix all database field issues'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                self.stdout.write('Fixing ALL database field issues...')
                
                # First, let's see what columns exist in the doctor table
                cursor.execute("PRAGMA table_info(adminapp_doctor)")
                columns = cursor.fetchall()
                existing_columns = [col[1] for col in columns]
                
                self.stdout.write(f'Existing doctor columns: {existing_columns}')
                
                # Fix all possible NULL values with appropriate defaults
                field_fixes = {
                    'average_rating': '0',
                    'total_reviews': '0', 
                    'total_appointments': '0',
                    'consultation_duration': '30',
                    'consultation_fee': '500.00',
                    'experience_years': '5',
                    'title': "'Dr.'",
                    'is_available': '1',
                    'is_verified': '0',
                    'is_featured': '0',
                    'education': "''",
                    'languages': "'English'",
                    'bio': "''",
                    'description': "''",
                    'license_number': "''",
                    'email': "''",
                    'phone': "''",  # Empty string for phone field
                    'first_name': "'Unknown'",
                    'last_name': "'Doctor'",
                }
                
                for field, default_value in field_fixes.items():
                    if field in existing_columns:
                        try:
                            cursor.execute(f"""
                                UPDATE adminapp_doctor 
                                SET {field} = {default_value} 
                                WHERE {field} IS NULL OR {field} = ''
                            """)
                            rows_affected = cursor.rowcount
                            if rows_affected > 0:
                                self.stdout.write(f'  ✅ Updated {rows_affected} records for {field}')
                        except Exception as e:
                            self.stdout.write(f'  ❌ Could not update {field}: {str(e)}')
                    else:
                        self.stdout.write(f'  ⚠️  Column {field} does not exist')
                
                # Fix timestamps
                timestamp_fields = ['created_at', 'updated_at']
                for field in timestamp_fields:
                    if field in existing_columns:
                        try:
                            cursor.execute(f"""
                                UPDATE adminapp_doctor 
                                SET {field} = datetime('now') 
                                WHERE {field} IS NULL
                            """)
                            rows_affected = cursor.rowcount
                            if rows_affected > 0:
                                self.stdout.write(f'  ✅ Updated {rows_affected} records for {field}')
                        except Exception as e:
                            self.stdout.write(f'  ❌ Could not update {field}: {str(e)}')
                
                # Now fix appointment table if zipcode doesn't exist
                cursor.execute("PRAGMA table_info(adminapp_appointment)")
                apt_columns = cursor.fetchall()
                apt_existing_columns = [col[1] for col in apt_columns]
                
                if 'zipcode' not in apt_existing_columns:
                    try:
                        cursor.execute("""
                            ALTER TABLE adminapp_appointment 
                            ADD COLUMN zipcode VARCHAR(10) DEFAULT ''
                        """)
                        self.stdout.write('  ✅ Added zipcode column to appointment table')
                    except Exception as e:
                        self.stdout.write(f'  ❌ Could not add zipcode column: {str(e)}')
                else:
                    self.stdout.write('  ✅ Zipcode column already exists')
                
                # Add description column to doctor if it doesn't exist
                if 'description' not in existing_columns:
                    try:
                        cursor.execute("""
                            ALTER TABLE adminapp_doctor 
                            ADD COLUMN description TEXT DEFAULT ''
                        """)
                        self.stdout.write('  ✅ Added description column to doctor table')
                    except Exception as e:
                        self.stdout.write(f'  ❌ Could not add description column: {str(e)}')
                else:
                    self.stdout.write('  ✅ Description column already exists')
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Successfully fixed ALL database field issues!')
                )
                
                # Show current counts
                cursor.execute("SELECT COUNT(*) FROM adminapp_doctor")
                doctor_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM adminapp_appointment")
                appointment_count = cursor.fetchone()[0]
                
                self.stdout.write(f'📊 Total doctors: {doctor_count}')
                self.stdout.write(f'📊 Total appointments: {appointment_count}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error fixing database: {str(e)}')
                )