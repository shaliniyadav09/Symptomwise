from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Clean up hospital-related tables that might be causing issues'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                self.stdout.write('Cleaning up hospital-related tables...')
                
                # List of tables that might need cleanup
                tables_to_check = [
                    'hospitals_hospitalinsurance',
                    'hospitals_hospitalrating', 
                    'hospitals_hospitalserviceoffering',
                    'hospitals_hospitalfacilityoffering'
                ]
                
                for table in tables_to_check:
                    try:
                        # Check if table exists
                        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                        if cursor.fetchone():
                            self.stdout.write(f'  Found table: {table}')
                            # Drop the table if it exists
                            cursor.execute(f"DROP TABLE IF EXISTS {table}")
                            self.stdout.write(f'  ✅ Dropped table: {table}')
                        else:
                            self.stdout.write(f'  ⚠️  Table {table} does not exist')
                    except Exception as e:
                        self.stdout.write(f'  ❌ Error with table {table}: {str(e)}')
                
                # Check for any remaining constraint issues
                try:
                    cursor.execute("PRAGMA foreign_key_check")
                    fk_issues = cursor.fetchall()
                    if fk_issues:
                        self.stdout.write(f'  ⚠️  Found {len(fk_issues)} foreign key issues')
                        for issue in fk_issues:
                            self.stdout.write(f'    {issue}')
                    else:
                        self.stdout.write('  ✅ No foreign key issues found')
                except Exception as e:
                    self.stdout.write(f'  Could not check foreign keys: {str(e)}')
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Hospital table cleanup completed!')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error during cleanup: {str(e)}')
                )