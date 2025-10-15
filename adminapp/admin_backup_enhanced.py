from django.contrib import admin
from .models import Category, Doctor, Appointment, MedicalSpecialty, DoctorAvailability, DoctorReview

# Safe admin configuration that handles broken references

@admin.register(MedicalSpecialty)
class MedicalSpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    
    def get_queryset(self, request):
        # Safe queryset that handles broken hospital references
        return super().get_queryset(request).select_related('hospital', 'specialty')

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_category_name', 'get_hospital_name', 'is_available']
    list_filter = ['is_available', 'is_verified', 'is_featured']
    search_fields = ['first_name', 'last_name', 'email']
    
    def get_full_name(self, obj):
        return f"{obj.title} {obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'
    
    def get_category_name(self, obj):
        try:
            return obj.category.name if obj.category else 'No Category'
        except:
            return 'Error'
    get_category_name.short_description = 'Category'
    
    def get_hospital_name(self, obj):
        try:
            return obj.hospital.name if obj.hospital else 'No Hospital'
        except:
            return 'Error'
    get_hospital_name.short_description = 'Hospital'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('hospital', 'category', 'specialty')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_id', 'get_patient_name', 'get_doctor_name', 'get_hospital_name', 'appointment_date', 'appointment_time', 'status']
    list_filter = ['status', 'appointment_date']
    search_fields = ['appointment_id', 'first_name', 'last_name', 'email']
    date_hierarchy = 'appointment_date'
    
    def get_patient_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_patient_name.short_description = 'Patient'
    
    def get_doctor_name(self, obj):
        try:
            return obj.doctor.full_name if obj.doctor else 'No Doctor'
        except:
            return 'Error'
    get_doctor_name.short_description = 'Doctor'
    
    def get_hospital_name(self, obj):
        try:
            return obj.hospital.name if obj.hospital else 'No Hospital'
        except:
            return 'Error - Broken Reference'
    get_hospital_name.short_description = 'Hospital'
    
    def get_queryset(self, request):
        # Use a safe queryset that doesn't fail on broken references
        try:
            return super().get_queryset(request).select_related('doctor', 'hospital')
        except:
            # Fallback to basic queryset if select_related fails
            return super().get_queryset(request)

@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['get_doctor_name', 'get_day_display', 'start_time', 'end_time', 'is_active']
    list_filter = ['day_of_week', 'is_active']
    
    def get_doctor_name(self, obj):
        try:
            return obj.doctor.full_name if obj.doctor else 'No Doctor'
        except:
            return 'Error'
    get_doctor_name.short_description = 'Doctor'
    
    def get_day_display(self, obj):
        return obj.get_day_of_week_display()
    get_day_display.short_description = 'Day'

@admin.register(DoctorReview)
class DoctorReviewAdmin(admin.ModelAdmin):
    list_display = ['patient_name', 'get_doctor_name', 'rating', 'is_verified', 'is_published', 'created_at']
    list_filter = ['rating', 'is_verified', 'is_published']
    search_fields = ['patient_name', 'patient_email']
    
    def get_doctor_name(self, obj):
        try:
            return obj.doctor.full_name if obj.doctor else 'No Doctor'
        except:
            return 'Error'
    get_doctor_name.short_description = 'Doctor'
