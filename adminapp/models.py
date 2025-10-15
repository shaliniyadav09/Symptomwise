from django.db import models
import secrets
import uuid
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from tenants.models import TenantAwareModel
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from .validators import validate_ten_digit_phone


# Medical Specialties - Global reference data
class MedicalSpecialty(models.Model):
    """
    Global medical specialties that can be used across all hospitals
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for AI matching")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Medical Specialties"
    
    def __str__(self):
        return self.name
    
    def get_keywords_list(self):
        return [k.strip() for k in self.keywords.split(',') if k.strip()]

# Hospital-specific categories (can map to specialties)
class Category(TenantAwareModel):
    """
    Hospital-specific categories that can map to global specialties
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    specialty = models.ForeignKey(MedicalSpecialty, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['hospital', 'name']
        ordering = ['name']
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return f"{self.name} ({self.hospital.name if self.hospital else 'No Hospital'})"

# In adminapp/models.py

class Doctor(TenantAwareModel):
    """
    Corrected Doctor model matching the latest database schema.
    """
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=20, default='Dr.')
    
    # Professional Information
   
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    specialty = models.ForeignKey(MedicalSpecialty, on_delete=models.SET_NULL, null=True, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    experience_years = models.IntegerField(default=5)
    education = models.TextField(help_text="Degrees, certifications, etc.", blank=True)
    languages = models.CharField(max_length=200, default="English", help_text="Comma-separated languages")
    
    # Contact & Profile
    email = models.EmailField(blank=True)
    phone = PhoneNumberField(
        blank=True, 
        region='IN',
        validators=[validate_ten_digit_phone] 
    )
    bio = models.TextField(blank=True, help_text="Professional biography")
    description = models.TextField(blank=True) # Field for additional details
    profile_image = models.ImageField(upload_to='doctor_profiles/', blank=True, null=True)
    
    # Consultation Details
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    consultation_duration = models.IntegerField(default=30, help_text="Duration in minutes")
    
    # Availability
    is_available = models.BooleanField(default=True)
    # The fields 'consultation_days', 'consultation_start_time', 'consultation_end_time' have been removed
    # as they are now handled by the DoctorAvailability model.
    
    # Ratings & Reviews
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.IntegerField(default=0)
    total_appointments = models.IntegerField(default=0)
    
    # Metadata
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # User account (optional)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    def get_languages_list(self):
        return [lang.strip() for lang in self.languages.split(',') if lang.strip()]
    
 

class DoctorAvailability(TenantAwareModel):
    """
    Detailed availability schedule for doctors
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['hospital', 'doctor', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.doctor.full_name} - {self.get_day_of_week_display()}: {self.start_time}-{self.end_time}"

class Appointment(TenantAwareModel):
    """
    Enhanced appointment model
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    # Appointment ID
    appointment_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Doctor and Patient Info
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Patient Details (for non-registered users)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = PhoneNumberField(
        region='IN', 
        validators=[validate_ten_digit_phone] 
    )
    email = models.EmailField()
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ])
    address = models.TextField(blank=True)
    zipcode = models.CharField(max_length=10, blank=True, help_text="Postal/ZIP code")
    
    # Appointment Details
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration = models.IntegerField(default=30, help_text="Duration in minutes")
    reason = models.TextField(blank=True, help_text="Reason for visit")
    symptoms = models.TextField(blank=True)
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Notes
    patient_notes = models.TextField(blank=True)
    doctor_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.appointment_id:
            self.appointment_id = f"APT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    class Meta:
        unique_together = [('hospital', 'doctor', 'appointment_date', 'appointment_time')]
        ordering = ['-appointment_date', '-appointment_time']
    
    def __str__(self):
        return f"{self.appointment_id} - {self.first_name} {self.last_name} with {self.doctor.full_name}"
    
    @property
    def patient_full_name(self):
        return f"{self.first_name} {self.last_name}"

class DoctorReview(TenantAwareModel):
    """
    Patient reviews for doctors
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reviews')
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    patient_name = models.CharField(max_length=100)
    patient_email = models.EmailField(blank=True)
    
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(blank=True)
    
    # Review aspects
    communication_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    treatment_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    facility_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    
    is_verified = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient_name} - {self.doctor.full_name} ({self.rating}/5)"