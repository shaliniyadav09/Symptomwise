from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix hospital field default values'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                self.stdout.write('Fixing hospital field issues...')
                
                # First, let's see what columns exist in the hospital table
                cursor.execute("PRAGMA table_info(tenants_hospital)")
                columns = cursor.fetchall()
                existing_columns = [col[1] for col in columns]
                
                self.stdout.write(f'Existing hospital columns: {existing_columns}')
                
                # Fix all possible NULL values with appropriate defaults
                field_fixes = {
                    'address': "'Default Address'",
                    'city': "'Default City'",
                    'state': "'Default State'",
                    'country': "'India'",
                    'postal_code': "'000000'",
                    'phone': "'+91-0000000000'",
                    'email': "'admin@hospital.com'",
                    'website': "''",
                    'description': "''",
                    'primary_color': "'#007bff'",
                    'secondary_color': "'#6c757d'",
                    'accent_color': "'#28a745'",
                    'logo_url': "''",
                    'theme_mode': "'light'",
                    'timezone': "'Asia/Kolkata'",
                    'language': "'en'",
                    'currency': "'INR'",
                    'working_hours': "'{}'",
                    'subscription_plan': "'trial'",
                    'max_doctors': "5",
                    'max_appointments_per_month': "100",
                    'ai_enabled': "1",
                    'whatsapp_enabled': "0",
                    'whatsapp_number': "''",
                    'payment_gateway_enabled': "0",
                    'razorpay_key_id': "''",
                    'razorpay_key_secret': "''",
                    'smtp_host': "''",
                    'smtp_port': "587",
                    'smtp_username': "''",
                    'smtp_password': "''",
                    'smtp_use_tls': "1",
                    'is_active': "1",
                    'is_verified': "1",
                }
                
                for field, default_value in field_fixes.items():
                    if field in existing_columns:
                        try:
                            cursor.execute(f"""
                                UPDATE tenants_hospital 
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
                                UPDATE tenants_hospital 
                                SET {field} = datetime('now') 
                                WHERE {field} IS NULL
                            """)
                            rows_affected = cursor.rowcount
                            if rows_affected > 0:
                                self.stdout.write(f'  ✅ Updated {rows_affected} records for {field}')
                        except Exception as e:
                            self.stdout.write(f'  ❌ Could not update {field}: {str(e)}')
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Successfully fixed hospital field issues!')
                )
                
                # Show current count
                cursor.execute("SELECT COUNT(*) FROM tenants_hospital")
                hospital_count = cursor.fetchone()[0]
                self.stdout.write(f'📊 Total hospitals: {hospital_count}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error fixing hospital fields: {str(e)}')
                )