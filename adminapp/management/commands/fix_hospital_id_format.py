from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = 'Fix hospital ID format by removing hyphens from references'

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
                # First, let's see what hospitals exist
                self.stdout.write('Current hospitals in database:')
                cursor.execute("SELECT id, name FROM tenants_hospital")
                hospitals = cursor.fetchall()
                for hospital in hospitals:
                    self.stdout.write(f'  ID: {hospital[0]}, Name: {hospital[1]}')
                
                # Check for appointments with hyphenated hospital IDs
                self.stdout.write('\nChecking for appointments with hyphenated hospital IDs...')
                
                cursor.execute("""
                    SELECT id, hospital_id, first_name, last_name 
                    FROM adminapp_appointment 
                    WHERE hospital_id LIKE '%-%'
                """)
                hyphenated_appointments = cursor.fetchall()
                
                if hyphenated_appointments:
                    self.stdout.write(f'Found {len(hyphenated_appointments)} appointments with hyphenated hospital IDs:')
                    
                    fixed_count = 0
                    for appointment in hyphenated_appointments:
                        appointment_id, old_hospital_id, first_name, last_name = appointment
                        # Remove hyphens from hospital ID
                        new_hospital_id = old_hospital_id.replace('-', '')
                        
                        self.stdout.write(f'  Appointment {appointment_id} ({first_name} {last_name}):')
                        self.stdout.write(f'    Old: {old_hospital_id}')
                        self.stdout.write(f'    New: {new_hospital_id}')
                        
                        # Check if the new hospital ID exists
                        cursor.execute("SELECT COUNT(*) FROM tenants_hospital WHERE id = %s", [new_hospital_id])
                        hospital_exists = cursor.fetchone()[0] > 0
                        
                        if hospital_exists:
                            if not dry_run:
                                cursor.execute("""
                                    UPDATE adminapp_appointment 
                                    SET hospital_id = %s 
                                    WHERE id = %s
                                """, [new_hospital_id, appointment_id])
                                fixed_count += 1
                            self.stdout.write(f'    ✅ Would fix (hospital exists)')
                        else:
                            self.stdout.write(f'    ❌ Hospital {new_hospital_id} does not exist')
                    
                    if not dry_run and fixed_count > 0:
                        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} appointment records'))
                else:
                    self.stdout.write(self.style.SUCCESS('No appointments with hyphenated hospital IDs found'))
                
                # Check for doctors with hyphenated hospital IDs
                self.stdout.write('\nChecking for doctors with hyphenated hospital IDs...')
                
                cursor.execute("""
                    SELECT id, hospital_id, first_name, last_name 
                    FROM adminapp_doctor 
                    WHERE hospital_id LIKE '%-%'
                """)
                hyphenated_doctors = cursor.fetchall()
                
                if hyphenated_doctors:
                    self.stdout.write(f'Found {len(hyphenated_doctors)} doctors with hyphenated hospital IDs:')
                    
                    fixed_count = 0
                    for doctor in hyphenated_doctors:
                        doctor_id, old_hospital_id, first_name, last_name = doctor
                        new_hospital_id = old_hospital_id.replace('-', '')
                        
                        self.stdout.write(f'  Doctor {doctor_id} ({first_name} {last_name}):')
                        self.stdout.write(f'    Old: {old_hospital_id}')
                        self.stdout.write(f'    New: {new_hospital_id}')
                        
                        cursor.execute("SELECT COUNT(*) FROM tenants_hospital WHERE id = %s", [new_hospital_id])
                        hospital_exists = cursor.fetchone()[0] > 0
                        
                        if hospital_exists:
                            if not dry_run:
                                cursor.execute("""
                                    UPDATE adminapp_doctor 
                                    SET hospital_id = %s 
                                    WHERE id = %s
                                """, [new_hospital_id, doctor_id])
                                fixed_count += 1
                            self.stdout.write(f'    ✅ Would fix (hospital exists)')
                        else:
                            self.stdout.write(f'    ❌ Hospital {new_hospital_id} does not exist')
                    
                    if not dry_run and fixed_count > 0:
                        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} doctor records'))
                else:
                    self.stdout.write(self.style.SUCCESS('No doctors with hyphenated hospital IDs found'))
                
                # Check other tables
                tables_to_check = [
                    ('adminapp_category', 'name'),
                    ('adminapp_doctoravailability', 'id'), 
                    ('adminapp_doctorreview', 'id')
                ]
                
                for table, name_field in tables_to_check:
                    try:
                        self.stdout.write(f'\nChecking {table}...')
                        cursor.execute(f"""
                            SELECT id, hospital_id, {name_field} 
                            FROM {table} 
                            WHERE hospital_id LIKE '%-%'
                        """)
                        hyphenated_records = cursor.fetchall()
                        
                        if hyphenated_records:
                            self.stdout.write(f'Found {len(hyphenated_records)} records with hyphenated hospital IDs')
                            
                            fixed_count = 0
                            for record in hyphenated_records:
                                record_id, old_hospital_id, name = record
                                new_hospital_id = old_hospital_id.replace('-', '')
                                
                                cursor.execute("SELECT COUNT(*) FROM tenants_hospital WHERE id = %s", [new_hospital_id])
                                hospital_exists = cursor.fetchone()[0] > 0
                                
                                if hospital_exists:
                                    if not dry_run:
                                        cursor.execute(f"""
                                            UPDATE {table} 
                                            SET hospital_id = %s 
                                            WHERE id = %s
                                        """, [new_hospital_id, record_id])
                                        fixed_count += 1
                            
                            if not dry_run and fixed_count > 0:
                                self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} records in {table}'))
                        else:
                            self.stdout.write(f'No hyphenated hospital IDs in {table}')
                    except Exception as e:
                        self.stdout.write(f'Could not check {table}: {str(e)}')
                
                if not dry_run:
                    self.stdout.write(self.style.SUCCESS('\nHospital ID format issues fixed!'))
                    self.stdout.write('You can now try running migrations again.')
                else:
                    self.stdout.write(self.style.WARNING('\nRun without --dry-run to apply fixes'))
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error fixing hospital ID format: {str(e)}')
                )
                raise