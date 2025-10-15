from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings


class Command(BaseCommand):
    help = 'Fix orphaned doctor references in database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        with connection.cursor() as cursor:
            try:
                # Check for orphaned appointments
                self.stdout.write('Checking for orphaned appointment records...')
                
                cursor.execute("""
                    SELECT COUNT(*) FROM adminapp_appointment 
                    WHERE doctor_id IS NOT NULL 
                    AND doctor_id NOT IN (SELECT id FROM adminapp_doctor)
                """)
                orphaned_appointments = cursor.fetchone()[0]
                
                if orphaned_appointments > 0:
                    self.stdout.write(
                        self.style.WARNING(f'Found {orphaned_appointments} orphaned appointment records')
                    )
                    
                    if not dry_run:
                        # Option 1: Set doctor_id to NULL for orphaned appointments
                        cursor.execute("""
                            UPDATE adminapp_appointment 
                            SET doctor_id = NULL 
                            WHERE doctor_id IS NOT NULL 
                            AND doctor_id NOT IN (SELECT id FROM adminapp_doctor)
                        """)
                        self.stdout.write(
                            self.style.SUCCESS(f'Fixed {orphaned_appointments} orphaned appointment records')
                        )
                    else:
                        self.stdout.write('Would set doctor_id to NULL for these appointments')
                else:
                    self.stdout.write(self.style.SUCCESS('No orphaned appointment records found'))
                
                # Check for orphaned doctor availability records
                self.stdout.write('Checking for orphaned doctor availability records...')
                
                cursor.execute("""
                    SELECT COUNT(*) FROM adminapp_doctoravailability 
                    WHERE doctor_id NOT IN (SELECT id FROM adminapp_doctor)
                """)
                orphaned_availability = cursor.fetchone()[0]
                
                if orphaned_availability > 0:
                    self.stdout.write(
                        self.style.WARNING(f'Found {orphaned_availability} orphaned availability records')
                    )
                    
                    if not dry_run:
                        cursor.execute("""
                            DELETE FROM adminapp_doctoravailability 
                            WHERE doctor_id NOT IN (SELECT id FROM adminapp_doctor)
                        """)
                        self.stdout.write(
                            self.style.SUCCESS(f'Deleted {orphaned_availability} orphaned availability records')
                        )
                    else:
                        self.stdout.write('Would delete these availability records')
                else:
                    self.stdout.write(self.style.SUCCESS('No orphaned availability records found'))
                
                # Check for orphaned doctor review records
                self.stdout.write('Checking for orphaned doctor review records...')
                
                cursor.execute("""
                    SELECT COUNT(*) FROM adminapp_doctorreview 
                    WHERE doctor_id NOT IN (SELECT id FROM adminapp_doctor)
                """)
                orphaned_reviews = cursor.fetchone()[0]
                
                if orphaned_reviews > 0:
                    self.stdout.write(
                        self.style.WARNING(f'Found {orphaned_reviews} orphaned review records')
                    )
                    
                    if not dry_run:
                        cursor.execute("""
                            DELETE FROM adminapp_doctorreview 
                            WHERE doctor_id NOT IN (SELECT id FROM adminapp_doctor)
                        """)
                        self.stdout.write(
                            self.style.SUCCESS(f'Deleted {orphaned_reviews} orphaned review records')
                        )
                    else:
                        self.stdout.write('Would delete these review records')
                else:
                    self.stdout.write(self.style.SUCCESS('No orphaned review records found'))
                
                # Show current doctor count
                cursor.execute("SELECT COUNT(*) FROM adminapp_doctor")
                doctor_count = cursor.fetchone()[0]
                self.stdout.write(f'Current doctor count: {doctor_count}')
                
                if not dry_run:
                    self.stdout.write(self.style.SUCCESS('Database integrity issues fixed!'))
                else:
                    self.stdout.write(self.style.WARNING('Run without --dry-run to apply fixes'))
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error fixing database: {str(e)}')
                )
                raise