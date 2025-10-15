from django.test import TestCase
from django.contrib.auth.models import User
from .models import Hospital, HospitalUser


class HospitalModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@hospital.com',
            email='testuser@hospital.com',
            password='testpass123'
        )
    
    def test_hospital_creation(self):
        hospital = Hospital.objects.create(
            name='Test Hospital',
            slug='test-hospital',
            subdomain='test',
            email='info@test.com',
            phone='+91 9876543210',
            address='Test Address',
            city='Mumbai',
            state='Maharashtra',
            country='India',
            postal_code='400001',
            owner=self.user
        )
        
        self.assertEqual(hospital.name, 'Test Hospital')
        self.assertEqual(hospital.subdomain, 'test')
        self.assertEqual(hospital.owner, self.user)
        self.assertTrue(hospital.is_active)
        self.assertFalse(hospital.is_verified)
    
    def test_hospital_user_relationship(self):
        hospital = Hospital.objects.create(
            name='Test Hospital',
            slug='test-hospital',
            subdomain='test',
            email='info@test.com',
            phone='+91 9876543210',
            address='Test Address',
            city='Mumbai',
            state='Maharashtra',
            country='India',
            postal_code='400001',
            owner=self.user
        )
        
        hospital_user = HospitalUser.objects.create(
            hospital=hospital,
            user=self.user,
            role='owner'
        )
        
        self.assertEqual(hospital_user.hospital, hospital)
        self.assertEqual(hospital_user.user, self.user)
        self.assertEqual(hospital_user.role, 'owner')
        self.assertTrue(hospital_user.is_active)