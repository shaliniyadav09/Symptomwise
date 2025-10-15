from django.contrib import admin
from django.utils.html import format_html
from .models import (
    MedicalSpecialty, Category, Doctor, DoctorAvailability,
    Appointment, DoctorReview
)

@admin.register(MedicalSpecialty)
class MedicalSpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'keywords']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'icon', 'is_active')
        }),
        ('AI Matching', {
            'fields': ('keywords',),
            'description': 'Comma-separated keywords for AI-powered doctor recommendations'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'hospital', 'specialty', 'is_active', 'created_at']
    list_filter = ['is_active', 'specialty', 'created_at']
    search_fields = ['name', 'description', 'hospital__name']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('hospital', 'specialty')

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'category', 'specialty', 'hospital', 
        'experience_years', 'average_rating', 'is_available', 'is_verified'
    ]
    list_filter = [
        'is_available', 'is_verified', 'is_featured', 'specialty',
        'category', 'experience_years', 'created_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'phone', 
        'license_number', 'hospital__name'
    ]
    readonly_fields = [
        'average_rating', 'total_reviews', 'total_appointments',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 'first_name', 'last_name', 'profile_image'
            )
        }),
        ('Professional Information', {
            'fields': (
                'category', 'specialty', 'license_number', 
                'experience_years', 'education', 'languages'
            )
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'bio')
        }),
        ('Consultation Details', {
            'fields': (
                'consultation_fee', 'consultation_duration',
                'consultation_days', 'consultation_start_time',
                'consultation_end_time'
            )
        }),
        ('Status & Settings', {
            'fields': (
                'is_available', 'is_verified', 'is_featured', 'user'
            )
        }),
        ('Statistics', {
            'fields': (
                'average_rating', 'total_reviews', 'total_appointments'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'hospital', 'category', 'specialty', 'user'
        )
    
    actions = ['mark_as_verified', 'mark_as_featured', 'mark_as_available']
    
    def mark_as_verified(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"Marked {queryset.count()} doctors as verified.")
    
    mark_as_verified.short_description = "Mark selected doctors as verified"
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"Marked {queryset.count()} doctors as featured.")
    
    mark_as_featured.short_description = "Mark selected doctors as featured"
    
    def mark_as_available(self, request, queryset):
        queryset.update(is_available=True)
        self.message_user(request, f"Marked {queryset.count()} doctors as available.")
    
    mark_as_available.short_description = "Mark selected doctors as available"

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = [
        'doctor', 'get_day_of_week_display', 'start_time', 
        'end_time', 'is_active'
    ]
    list_filter = ['day_of_week', 'is_active', 'doctor__hospital']
    search_fields = ['doctor__first_name', 'doctor__last_name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('doctor', 'hospital')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'appointment_id', 'patient_full_name', 'doctor', 
        'appointment_date', 'appointment_time', 'status', 'is_paid'
    ]
    list_filter = [
        'status', 'is_paid', 'appointment_date', 'gender',
        'doctor__category', 'created_at'
    ]
    search_fields = [
        'appointment_id', 'first_name', 'last_name', 'email', 
        'phone', 'doctor__first_name', 'doctor__last_name'
    ]
    readonly_fields = [
        'appointment_id', 'created_at', 'updated_at', 'confirmed_at'
    ]
    
    fieldsets = (
        ('Appointment Details', {
            'fields': (
                'appointment_id', 'doctor', 'appointment_date', 
                'appointment_time', 'duration', 'status'
            )
        }),
        ('Patient Information', {
            'fields': (
                'patient_user', 'first_name', 'last_name', 'email', 
                'phone', 'date_of_birth', 'gender', 'address'
            )
        }),
        ('Medical Information', {
            'fields': ('reason', 'symptoms', 'patient_notes')
        }),
        ('Payment & Billing', {
            'fields': (
                'consultation_fee', 'is_paid', 'payment_method'
            )
        }),
        ('Doctor Notes', {
            'fields': ('doctor_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'doctor', 'patient_user', 'hospital'
        )
    
    actions = ['confirm_appointments', 'mark_as_completed', 'mark_as_paid']
    
    def confirm_appointments(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status='scheduled').update(
            status='confirmed',
            confirmed_at=timezone.now()
        )
        self.message_user(request, f"Confirmed {queryset.count()} appointments.")
    
    confirm_appointments.short_description = "Confirm selected appointments"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"Marked {queryset.count()} appointments as completed.")
    
    mark_as_completed.short_description = "Mark selected appointments as completed"
    
    def mark_as_paid(self, request, queryset):
        queryset.update(is_paid=True)
        self.message_user(request, f"Marked {queryset.count()} appointments as paid.")
    
    mark_as_paid.short_description = "Mark selected appointments as paid"

@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = [
        'doctor', 'patient_name', 'rating', 'is_verified', 
        'is_published', 'created_at'
    ]
    list_filter = [
        'rating', 'is_verified', 'is_published', 'created_at',
        'doctor__category', 'doctor__hospital'
    ]
    search_fields = [
        'doctor__first_name', 'doctor__last_name', 'patient_name', 
        'review_text'
    ]
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Review Information', {
            'fields': (
                'doctor', 'appointment', 'patient_name', 'patient_email'
            )
        }),
        ('Ratings', {
            'fields': (
                'rating', 'communication_rating', 'treatment_rating', 
                'facility_rating'
            )
        }),
        ('Review Content', {
            'fields': ('review_text',)
        }),
        ('Moderation', {
            'fields': ('is_verified', 'is_published')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'doctor', 'appointment', 'hospital'
        )
    
    actions = ['verify_reviews', 'publish_reviews']
    
    def verify_reviews(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"Verified {queryset.count()} reviews.")
    
    verify_reviews.short_description = "Verify selected reviews"
    
    def publish_reviews(self, request, queryset):
        queryset.update(is_published=True)
        self.message_user(request, f"Published {queryset.count()} reviews.")
    
    publish_reviews.short_description = "Publish selected reviews"

# Note: Models are already registered using @admin.register() decorators above
# No need for additional admin.site.register() calls