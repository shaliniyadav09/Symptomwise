from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix doctor default values for rating fields'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # Set default values for any NULL rating fields
                cursor.execute("""
                    UPDATE adminapp_doctor 
                    SET average_rating = 0 
                    WHERE average_rating IS NULL
                """)
                
                cursor.execute("""
                    UPDATE adminapp_doctor 
                    SET total_reviews = 0 
                    WHERE total_reviews IS NULL
                """)
                
                cursor.execute("""
                    UPDATE adminapp_doctor 
                    SET total_appointments = 0 
                    WHERE total_appointments IS NULL
                """)
                
                self.stdout.write(
                    self.style.SUCCESS('Successfully fixed doctor default values')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error fixing doctor defaults: {str(e)}')
                )