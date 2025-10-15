from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from adminapp.models import MedicalSpecialty
from hospitals.models import HospitalService, HospitalFacility
from tenants.models import Hospital
import uuid

class Command(BaseCommand):
    help = 'Setup the healthcare platform with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-demo-hospital',
            action='store_true',
            help='Create a demo hospital with sample data',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🏥 Setting up Healthcare Platform...')
        )

        # Create medical specialties
        self.create_medical_specialties()
        
        # Create hospital services
        self.create_hospital_services()
        
        # Create hospital facilities
        self.create_hospital_facilities()
        
        if options['create_demo_hospital']:
            self.create_demo_hospital()

        self.stdout.write(
            self.style.SUCCESS('✅ Healthcare Platform setup completed!')
        )

    def create_medical_specialties(self):
        """Create medical specialties"""
        specialties = [
            ('Cardiology', 'Heart and cardiovascular system', 'heart,cardiac,chest pain,blood pressure'),
            ('Neurology', 'Brain and nervous system', 'brain,headache,migraine,seizure,stroke'),
            ('Orthopedics', 'Bones and joints', 'bone,joint,fracture,back pain,arthritis'),
            ('Dermatology', 'Skin conditions', 'skin,rash,acne,allergy,eczema'),
            ('Pediatrics', 'Children\'s health', 'child,baby,infant,pediatric,vaccination'),
            ('Gynecology', 'Women\'s health', 'women,pregnancy,menstrual,gynecological'),
            ('General Medicine', 'General healthcare', 'fever,cold,flu,general,checkup'),
        ]

        created_count = 0
        for name, description, keywords in specialties:
            specialty, created = MedicalSpecialty.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'keywords': keywords,
                    'is_active': True
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'📋 Created {created_count} medical specialties')

    def create_hospital_services(self):
        """Create hospital services"""
        services = [
            ('Emergency Care', 'emergency', '24/7 emergency medical services'),
            ('X-Ray', 'diagnostic', 'Digital X-ray imaging'),
            ('Blood Tests', 'diagnostic', 'Comprehensive blood testing'),
            ('General Surgery', 'surgical', 'General surgical procedures'),
            ('Pharmacy', 'support', 'In-house pharmacy services'),
        ]

        created_count = 0
        for name, category, description in services:
            service, created = HospitalService.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'description': description,
                    'is_active': True
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'🏥 Created {created_count} hospital services')

    def create_hospital_facilities(self):
        """Create hospital facilities"""
        facilities = [
            ('ICU', 'medical', 'Intensive Care Unit'),
            ('Private Rooms', 'comfort', 'Private patient rooms'),
            ('WiFi', 'comfort', 'Free wireless internet'),
            ('Parking', 'parking', 'Patient and visitor parking'),
            ('Cafeteria', 'food', 'Hospital cafeteria'),
        ]

        created_count = 0
        for name, category, description in facilities:
            facility, created = HospitalFacility.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'description': description
                }
            )
            if created:
                created_count += 1

        self.stdout.write(f'🏢 Created {created_count} hospital facilities')

    def create_demo_hospital(self):
        """Create a demo hospital for testing"""
        # Create demo user
        demo_user, created = User.objects.get_or_create(
            username='demo_hospital_admin',
            defaults={
                'email': 'demo@hospital.com',
                'first_name': 'Demo',
                'last_name': 'Admin',
                'is_staff': False
            }
        )

        if created:
            demo_user.set_password('demo123')
            demo_user.save()

        # Create demo hospital
        demo_hospital, created = Hospital.objects.get_or_create(
            subdomain='demo-hospital',
            defaults={
                'name': 'Demo General Hospital',
                'slug': 'demo-general-hospital',
                'email': 'info@demohospital.com',
                'phone': '+91 9876543210',
                'address': '123 Healthcare Street, Medical District',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'country': 'India',
                'postal_code': '400001',
                'owner': demo_user,
                'is_active': True,
                'is_verified': True
            }
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS('🏥 Created demo hospital: Demo General Hospital')
            )
            self.stdout.write(f'   Subdomain: demo-hospital')
            self.stdout.write(f'   Admin user: demo_hospital_admin / demo123')
        else:
            self.stdout.write('⚠️  Demo hospital already exists')