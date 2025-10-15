from django.core.management.base import BaseCommand
from django.db import connection
from adminapp.models import Doctor

class Command(BaseCommand):
    help = 'Check the Doctor table schema'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Get table info
            cursor.execute("PRAGMA table_info(adminapp_doctor);")
            columns = cursor.fetchall()
            
            self.stdout.write("Doctor table schema:")
            for column in columns:
                self.stdout.write(f"  {column[1]} - {column[2]} - NOT NULL: {column[3]} - Default: {column[4]}")
            
            # Check if there's an 'experience' field
            experience_fields = [col for col in columns if 'experience' in col[1].lower()]
            if experience_fields:
                self.stdout.write("\nExperience-related fields:")
                for field in experience_fields:
                    self.stdout.write(f"  {field[1]} - {field[2]} - NOT NULL: {field[3]}")
            
            # Try to get a sample doctor
            try:
                doctor = Doctor.objects.first()
                if doctor:
                    self.stdout.write(f"\nSample doctor: {doctor.full_name}")
                    self.stdout.write(f"Experience years: {doctor.experience_years}")
                else:
                    self.stdout.write("\nNo doctors found in database")
            except Exception as e:
                self.stdout.write(f"\nError getting sample doctor: {e}")