from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings


class Command(BaseCommand):
    help = 'Fix orphaned hospital references in database'

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
                # Check for orphaned appointments with invalid hospital_id
                self.stdout.write('Checking for orphaned appointment records with invalid hospital_id...')
                
                cursor.execute("""
                    SELECT COUNT(*) FROM adminapp_appointment 
                    WHERE hospital_id IS NOT NULL 
                    AND hospital_id NOT IN (SELECT id FROM tenants_hospital)
                """)
                orphaned_appointments = cursor.fetchone()[0]
                
                if orphaned_appointments > 0:
                    self.stdout.write(
                        self.style.WARNING(f'Found {orphaned_appointments} appointments with invalid hospital_id')
                    )
                    
                    # Show the problematic records
                    cursor.execute("""
                        SELECT id, hospital_id, first_name, last_name, appointment_date 
                        FROM adminapp_appointment 
                        WHERE hospital_id IS NOT NULL 
                        AND hospital_id NOT IN (SELECT id FROM tenants_hospital)
                        LIMIT 10
                    """)
                    problematic_records = cursor.fetchall()
                    
                    self.stdout.write('Problematic records:')
                    for record in problematic_records:
                        self.stdout.write(f'  ID: {record[0]}, Hospital ID: {record[1]}, Patient: {record[2]} {record[3]}, Date: {record[4]}')
                    
                    if not dry_run:
                        # Get the first available hospital ID
                        cursor.execute("SELECT id FROM tenants_hospital LIMIT 1")
                        first_hospital = cursor.fetchone()
                        
                        if first_hospital:
                            first_hospital_id = first_hospital[0]
                            self.stdout.write(f'Setting orphaned appointments to hospital: {first_hospital_id}')
                            
                            cursor.execute("""
                                UPDATE adminapp_appointment 
                                SET hospital_id = %s 
                                WHERE hospital_id IS NOT NULL 
                                AND hospital_id NOT IN (SELECT id FROM tenants_hospital)
                            """, [first_hospital_id])
                            
                            self.stdout.write(
                                self.style.SUCCESS(f'Fixed {orphaned_appointments} orphaned appointment records')
                            )
                        else:
                            # No hospitals exist, set to NULL
                            cursor.execute("""
                                UPDATE adminapp_appointment 
                                SET hospital_id = NULL 
                                WHERE hospital_id IS NOT NULL 
                                AND hospital_id NOT IN (SELECT id FROM tenants_hospital)
                            """)
                            self.stdout.write(
                                self.style.SUCCESS(f'Set hospital_id to NULL for {orphaned_appointments} appointments (no hospitals found)')
                            )
                    else:
                        self.stdout.write('Would fix these appointment records')
                else:
                    self.stdout.write(self.style.SUCCESS('No orphaned appointment records found'))
                
                # Check for orphaned doctors with invalid hospital_id
                self.stdout.write('Checking for orphaned doctor records with invalid hospital_id...')
                
                cursor.execute("""
                    SELECT COUNT(*) FROM adminapp_doctor 
                    WHERE hospital_id IS NOT NULL 
                    AND hospital_id NOT IN (SELECT id FROM tenants_hospital)
                """)
                orphaned_doctors = cursor.fetchone()[0]
                
                if orphaned_doctors > 0:
                    self.stdout.write(
                        self.style.WARNING(f'Found {orphaned_doctors} doctors with invalid hospital_id')
                    )
                    
                    if not dry_run:
                        # Get the first available hospital ID
                        cursor.execute("SELECT id FROM tenants_hospital LIMIT 1")
                        first_hospital = cursor.fetchone()
                        
                        if first_hospital:
                            first_hospital_id = first_hospital[0]
                            cursor.execute("""
                                UPDATE adminapp_doctor 
                                SET hospital_id = %s 
                                WHERE hospital_id IS NOT NULL 
                                AND hospital_id NOT IN (SELECT id FROM tenants_hospital)
                            """, [first_hospital_id])
                            
                            self.stdout.write(
                                self.style.SUCCESS(f'Fixed {orphaned_doctors} orphaned doctor records')
                            )
                        else:
                            cursor.execute("""
                                UPDATE adminapp_doctor 
                                SET hospital_id = NULL 
                                WHERE hospital_id IS NOT NULL 
                                AND hospital_id NOT IN (SELECT id FROM tenants_hospital)
                            """)
                            self.stdout.write(
                                self.style.SUCCESS(f'Set hospital_id to NULL for {orphaned_doctors} doctors')
                            )
                    else:
                        self.stdout.write('Would fix these doctor records')
                else:
                    self.stdout.write(self.style.SUCCESS('No orphaned doctor records found'))
                
                # Check other tables that might have hospital_id
                tables_to_check = [
                    'adminapp_category',
                    'adminapp_doctoravailability', 
                    'adminapp_doctorreview'
                ]
                
                for table in tables_to_check:
                    try:
                        cursor.execute(f"""
                            SELECT COUNT(*) FROM {table} 
                            WHERE hospital_id IS NOT NULL 
                            AND hospital_id NOT IN (SELECT id FROM tenants_hospital)
                        """)
                        orphaned_count = cursor.fetchone()[0]
                        
                        if orphaned_count > 0:
                            self.stdout.write(
                                self.style.WARNING(f'Found {orphaned_count} orphaned records in {table}')
                            )
                            
                            if not dry_run:
                                cursor.execute("SELECT id FROM tenants_hospital LIMIT 1")
                                first_hospital = cursor.fetchone()
                                
                                if first_hospital:
                                    first_hospital_id = first_hospital[0]
                                    cursor.execute(f"""
                                        UPDATE {table} 
                                        SET hospital_id = %s 
                                        WHERE hospital_id IS NOT NULL 
                                        AND hospital_id NOT IN (SELECT id FROM tenants_hospital)
                                    """, [first_hospital_id])
                                else:
                                    cursor.execute(f"""
                                        UPDATE {table} 
                                        SET hospital_id = NULL 
                                        WHERE hospital_id IS NOT NULL 
                                        AND hospital_id NOT IN (SELECT id FROM tenants_hospital)
                                    """)
                                
                                self.stdout.write(
                                    self.style.SUCCESS(f'Fixed {orphaned_count} records in {table}')
                                )
                        else:
                            self.stdout.write(self.style.SUCCESS(f'No orphaned records in {table}'))
                    except Exception as e:
                        self.stdout.write(f'Could not check {table}: {str(e)}')
                
                # Show current hospital count
                cursor.execute("SELECT COUNT(*) FROM tenants_hospital")
                hospital_count = cursor.fetchone()[0]
                self.stdout.write(f'Current hospital count: {hospital_count}')
                
                if hospital_count == 0:
                    self.stdout.write(self.style.ERROR('WARNING: No hospitals found in database!'))
                    self.stdout.write('You may need to create a hospital first.')
                
                if not dry_run:
                    self.stdout.write(self.style.SUCCESS('Database hospital reference issues fixed!'))
                else:
                    self.stdout.write(self.style.WARNING('Run without --dry-run to apply fixes'))
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error fixing database: {str(e)}')
                )
                raise