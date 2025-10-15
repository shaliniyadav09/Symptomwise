from django.db import models
from tenants.models import TenantAwareModel
from django.utils import timezone

class HospitalFacility(TenantAwareModel):
    """
    Hospital facilities and amenities
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Hospital Facilities"
    
    def __str__(self):
        return f"{self.name} - {self.hospital.name if self.hospital else 'No Hospital'}"


class HospitalRegistration(TenantAwareModel):
    """
    Hospital registration and licensing information
    """
    registration_number = models.CharField(max_length=100, unique=True)
    # FIX: Added default for existing rows (since it was non-nullable)
    registration_date = models.DateField(default=timezone.now) 
    expiry_date = models.DateField(null=True, blank=True)
    # Note: 'hospital_name' was renamed to 'issuing_authority' in the previous steps
    issuing_authority = models.CharField(max_length=200) 
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-registration_date']
    
    def __str__(self):
        return f"{self.registration_number} - {self.hospital.name if self.hospital else 'No Hospital'}"


class HospitalContact(TenantAwareModel):
    """
    Hospital contact information
    """
    CONTACT_TYPES = [
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('fax', 'Fax'),
        ('emergency', 'Emergency'),
        ('appointment', 'Appointment'),
    ]
    
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES)
    # FIX: Added default for existing rows (since it was non-nullable)
    contact_value = models.CharField(max_length=200, default='N/A') 
    # Note: 'available_24x7' was renamed to 'is_primary' in the previous steps
    is_primary = models.BooleanField(default=False) 
    # Note: 'is_active' was renamed to 'is_public' in the previous steps
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['contact_type', '-is_primary']
    
    def __str__(self):
        return f"{self.get_contact_type_display()}: {self.contact_value}"

class HospitalService(TenantAwareModel):
    """
    Services offered by the hospital
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_emergency = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.hospital.name if self.hospital else 'No Hospital'}"
