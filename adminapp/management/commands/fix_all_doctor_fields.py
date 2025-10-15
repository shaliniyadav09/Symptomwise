from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix all doctor field default values'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                self.stdout.write('Fixing doctor field defaults...')
                
                # Set default values for all fields that might be NULL
                updates = [
                    ("average_rating", "0"),
                    ("total_reviews", "0"), 
                    ("total_appointments", "0"),
                    ("consultation_duration", "30"),
                    ("consultation_fee", "500.00"),
                    ("experience_years", "5"),
                    ("title", "'Dr.'"),
                    ("is_available", "1"),
                    ("is_verified", "0"),
                    ("is_featured", "0"),
                ]
                
                for field, default_value in updates:
                    try:
                        cursor.execute(f"""
                            UPDATE adminapp_doctor 
                            SET {field} = {default_value} 
                            WHERE {field} IS NULL
                        """)
                        rows_affected = cursor.rowcount
                        if rows_affected > 0:
                            self.stdout.write(f'  Updated {rows_affected} records for {field}')
                    except Exception as e:
                        self.stdout.write(f'  Could not update {field}: {str(e)}')
                
                # Set empty strings for text fields
                text_fields = [
                    ("education", "''"),
                    ("languages", "'English'"),
                    ("bio", "''"),
                    ("description", "''"),
                    ("license_number", "''"),
                    ("email", "''"),
                ]
                
                for field, default_value in text_fields:
                    try:
                        cursor.execute(f"""
                            UPDATE adminapp_doctor 
                            SET {field} = {default_value} 
                            WHERE {field} IS NULL
                        """)
                        rows_affected = cursor.rowcount
                        if rows_affected > 0:
                            self.stdout.write(f'  Updated {rows_affected} records for {field}')
                    except Exception as e:
                        self.stdout.write(f'  Could not update {field}: {str(e)}')
                
                # Add created_at and updated_at if they don't exist
                try:
                    cursor.execute("""
                        UPDATE adminapp_doctor 
                        SET created_at = datetime('now') 
                        WHERE created_at IS NULL
                    """)
                    cursor.execute("""
                        UPDATE adminapp_doctor 
                        SET updated_at = datetime('now') 
                        WHERE updated_at IS NULL
                    """)
                except Exception as e:
                    self.stdout.write(f'  Could not update timestamps: {str(e)}')
                
                self.stdout.write(
                    self.style.SUCCESS('Successfully fixed all doctor field defaults')
                )
                
                # Show current doctor count
                cursor.execute("SELECT COUNT(*) FROM adminapp_doctor")
                count = cursor.fetchone()[0]
                self.stdout.write(f'Total doctors in database: {count}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error fixing doctor fields: {str(e)}')
                )