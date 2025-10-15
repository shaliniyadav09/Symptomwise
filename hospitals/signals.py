"""
Django signals for the hospitals app
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import HospitalRegistration, HospitalRating
from tenants.models import Hospital, HospitalUser


@receiver(post_save, sender=HospitalRegistration)
def handle_hospital_registration(sender, instance, created, **kwargs):
    """
    Handle hospital registration approval process
    """
    if created:
        # Send notification email to admins about new registration
        # This can be expanded to send actual emails
        print(f"New hospital registration: {instance.hospital_name}")
    
    # If status changed to approved, create the actual Hospital
    if instance.status == 'approved' and not instance.hospital:
        try:
            # Create the Hospital instance
            hospital = Hospital.objects.create(
                name=instance.hospital_name,
                slug=instance.preferred_subdomain,
                subdomain=instance.preferred_subdomain,
                email=instance.email,
                phone=instance.phone,
                address=instance.address,
                city=instance.city,
                state=instance.state,
                country=instance.country,
                postal_code=instance.postal_code,
                owner_id=1,  # Default to admin user, should be updated
                is_active=True,
                is_verified=True
            )
            
            # Link the registration to the created hospital
            instance.hospital = hospital
            instance.save()
            
            print(f"Hospital created: {hospital.name}")
            
        except Exception as e:
            print(f"Error creating hospital: {e}")


@receiver(post_save, sender=HospitalRating)
def update_hospital_rating(sender, instance, created, **kwargs):
    """
    Update hospital average rating when a new rating is added
    """
    if created and instance.is_published:
        hospital = instance.hospital
        
        # Calculate new average rating
        ratings = HospitalRating.objects.filter(
            hospital=hospital,
            is_published=True
        )
        
        if ratings.exists():
            total_ratings = ratings.count()
            avg_overall = sum(r.overall_rating for r in ratings) / total_ratings
            avg_cleanliness = sum(r.cleanliness_rating for r in ratings) / total_ratings
            avg_staff = sum(r.staff_rating for r in ratings) / total_ratings
            avg_facilities = sum(r.facilities_rating for r in ratings) / total_ratings
            avg_value = sum(r.value_rating for r in ratings) / total_ratings
            
            # You can store these averages in a separate model or cache
            # For now, we'll just print them
            print(f"Updated ratings for {hospital.name}:")
            print(f"  Overall: {avg_overall:.1f}")
            print(f"  Cleanliness: {avg_cleanliness:.1f}")
            print(f"  Staff: {avg_staff:.1f}")
            print(f"  Facilities: {avg_facilities:.1f}")
            print(f"  Value: {avg_value:.1f}")


@receiver(pre_delete, sender=Hospital)
def cleanup_hospital_data(sender, instance, **kwargs):
    """
    Cleanup related data when a hospital is deleted
    """
    print(f"Cleaning up data for hospital: {instance.name}")
    
    # Archive related registrations instead of deleting
    HospitalRegistration.objects.filter(hospital=instance).update(
        status='archived'
    )


# Additional signals can be added here for:
# - Doctor profile updates
# - Appointment notifications
# - Email notifications
# - Analytics tracking
# etc.