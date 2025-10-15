from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField
import uuid


class Hospital(models.Model):
    """
    Hospital/Tenant model for multi-tenancy support
    Each hospital is a separate tenant with its own branding and configuration
    """
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Hospital/Clinic Name")
    slug = models.SlugField(unique=True, help_text="URL-friendly identifier")
    subdomain = models.CharField(
        max_length=50, 
        unique=True, 
        validators=[RegexValidator(r'^[a-z0-9-]+$', 'Only lowercase letters, numbers, and hyphens allowed')],
        help_text="Subdomain for hospital (e.g., apollo.yourdomain.com)"
    )
    
    # Contact Information
    email = models.EmailField()
    phone = PhoneNumberField(region="IN")
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=20)
    
    # Branding & Customization
    logo = models.ImageField(upload_to='hospital_logos/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default="#007bff", help_text="Hex color code")
    secondary_color = models.CharField(max_length=7, default="#6c757d", help_text="Hex color code")
    website = models.URLField(blank=True)
    
    # Configuration
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    language = models.CharField(max_length=10, default="en")
    currency = models.CharField(max_length=3, default="INR")
    
    # Working Hours (JSON field for flexibility)
    working_hours = models.JSONField(
        default=dict,
        help_text='Example: {"Monday": "9:00-17:00", "Tuesday": "9:00-17:00"}'
    )
    
    # Features & Subscriptions
    subscription_plan = models.CharField(
        max_length=20,
        choices=[
            ('trial', 'Trial'),
            ('basic', 'Basic'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise'),
        ],
        default='trial'
    )
    max_doctors = models.IntegerField(default=5, help_text="Maximum number of doctors allowed")
    max_appointments_per_month = models.IntegerField(default=100)
    
    # AI & Chatbot Settings
    ai_enabled = models.BooleanField(default=True)
    whatsapp_enabled = models.BooleanField(default=False)
    whatsapp_number = PhoneNumberField(region="IN", blank=True)
    
    # Payment & Billing
    payment_gateway_enabled = models.BooleanField(default=False)
    razorpay_key_id = models.CharField(max_length=100, blank=True)
    razorpay_key_secret = models.CharField(max_length=100, blank=True)
    
    # Email Configuration
    smtp_host = models.CharField(max_length=100, blank=True)
    smtp_port = models.IntegerField(default=587)
    smtp_username = models.CharField(max_length=100, blank=True)
    smtp_password = models.CharField(max_length=100, blank=True)
    smtp_use_tls = models.BooleanField(default=True)
    
    # Status & Metadata
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Owner/Admin
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_hospitals')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Hospital'
        verbose_name_plural = 'Hospitals'
    
    def __str__(self):
        return self.name
    
    @property
    def is_trial_expired(self):
        if self.subscription_plan == 'trial' and self.trial_ends_at:
            from django.utils import timezone
            return timezone.now() > self.trial_ends_at
        return False
    
    def get_absolute_url(self):
        return f"https://{self.subdomain}.yourdomain.com"

    @property
    def get_formatted_working_hours(self):
        """
        Parses the working_hours JSON and returns a list of tuples.
        """
        if not self.working_hours or not isinstance(self.working_hours, dict):
            return []
        
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Sort the hours based on the days_order list
        sorted_hours = sorted(
            self.working_hours.items(),
            key=lambda item: days_order.index(item[0]) if item[0] in days_order else 99
        )
        return sorted_hours

class HospitalUser(models.Model):
    """
    Association between users and hospitals with roles
    Supports multi-hospital access for users
    """
    
    ROLE_CHOICES = [
        ('owner', 'Hospital Owner'),
        ('admin', 'Hospital Admin'),
        ('manager', 'Department Manager'),
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist'),
        ('staff', 'Staff'),
    ]
    
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='hospital_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hospital_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['hospital', 'user']
        ordering = ['hospital', 'role', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.hospital.name} ({self.role})"


class TenantAwareManager(models.Manager):
    """
    Custom manager to automatically filter by current tenant
    """
    
    def get_queryset(self):
        from .middleware import get_current_hospital
        hospital = get_current_hospital()
        if hospital:
            return super().get_queryset().filter(hospital=hospital)
        return super().get_queryset()


class TenantAwareModel(models.Model):
    """
    Abstract base model for tenant-aware models
    """
    
    hospital = models.ForeignKey(
        Hospital, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Hospital this record belongs to"
    )
    
    objects = models.Manager()  # Default manager (no filtering)
    tenant_objects = TenantAwareManager()  # Tenant-aware manager
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        # Auto-assign current hospital if not set
        if not self.hospital_id:
            from .middleware import get_current_hospital
            hospital = get_current_hospital()
            if hospital:
                self.hospital = hospital
        super().save(*args, **kwargs)