from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
from .models import Category, Doctor, Appointment, MedicalSpecialty

# Import models that might not exist yet
try:
    from .models import DoctorAvailability, DoctorReview
    DOCTORAVAILABILITY_EXISTS = True
    DOCTORREVIEW_EXISTS = True
except ImportError:
    DoctorAvailability = None
    DoctorReview = None
    DOCTORAVAILABILITY_EXISTS = False
    DOCTORREVIEW_EXISTS = False

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
        try:
            return super().get_queryset(request).select_related('hospital', 'specialty')
        except:
            return super().get_queryset(request)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_category_name', 'get_hospital_name', 'is_available']
    list_filter = ['is_available', 'is_verified', 'is_featured']
    search_fields = ['first_name', 'last_name', 'email']
    
    def get_full_name(self, obj):
        try:
            return f"{obj.title} {obj.first_name} {obj.last_name}"
        except:
            return "Error"
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
        try:
            return super().get_queryset(request).select_related('hospital', 'category', 'specialty')
        except:
            return super().get_queryset(request)

class AppointmentAdminForm(forms.ModelForm):
    """Custom form for appointment admin"""
    
    class Meta:
        model = Appointment
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        try:
            from tenants.models import Hospital
            
            hospitals = Hospital.objects.all()
            if hospitals.exists():
                self.fields['hospital'].queryset = hospitals
                if not self.instance.pk:
                    self.fields['hospital'].initial = hospitals.first()
            else:
                self.fields['hospital'].queryset = Hospital.objects.none()
                self.fields['hospital'].help_text = "No hospitals available. Please create a hospital first."
            
            doctors = Doctor.objects.select_related('hospital').all()
            valid_doctors = []
            for doctor in doctors:
                try:
                    hospital_name = doctor.hospital.name if doctor.hospital else None
                    valid_doctors.append(doctor.id)
                except:
                    pass
            
            if valid_doctors:
                self.fields['doctor'].queryset = Doctor.objects.filter(id__in=valid_doctors)
            else:
                self.fields['doctor'].queryset = Doctor.objects.none()
                self.fields['doctor'].help_text = "No doctors with valid hospitals available."
                
        except Exception as e:
            pass
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not cleaned_data.get('status'):
            cleaned_data['status'] = 'scheduled'
        
        if not cleaned_data.get('duration'):
            cleaned_data['duration'] = 30
        
        if not cleaned_data.get('consultation_fee'):
            cleaned_data['consultation_fee'] = 500.00
        
        return cleaned_data

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    form = AppointmentAdminForm
    
    list_display = [
        'appointment_id', 
        'get_patient_name', 
        'get_doctor_name', 
        'get_hospital_name', 
        'appointment_date', 
        'appointment_time', 
        'get_status_display_safe'
    ]
    list_filter = ['status', 'appointment_date']
    search_fields = ['appointment_id', 'first_name', 'last_name', 'email', 'phone']
    date_hierarchy = 'appointment_date'
    actions = ['mark_as_confirmed', 'mark_as_completed', 'mark_as_cancelled', 'mark_as_no_show']
    
    fieldsets = (
        ('Patient Information', {
            'fields': ('first_name', 'last_name', 'phone', 'email', 'date_of_birth', 'gender', 'address')
        }),
        ('Appointment Details', {
            'fields': ('hospital', 'doctor', 'appointment_date', 'appointment_time', 'duration', 'reason', 'symptoms')
        }),
        ('Status & Payment', {
            'fields': ('status', 'consultation_fee', 'is_paid', 'payment_method')
        }),
        ('Notes', {
            'fields': ('patient_notes', 'doctor_notes'),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('patient_user', 'confirmed_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_patient_name(self, obj):
        try:
            return f"{obj.first_name} {obj.last_name}"
        except:
            return "Error"
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
            return 'Error'
    get_hospital_name.short_description = 'Hospital'
    
    def get_status_display_safe(self, obj):
        try:
            if not hasattr(obj, 'status'):
                return 'Unknown'
            
            status = obj.status
            status_colors = {
                'scheduled': '#ffc107',
                'confirmed': '#17a2b8',
                'in_progress': '#fd7e14',
                'completed': '#28a745',
                'cancelled': '#dc3545',
                'no_show': '#6c757d',
            }
            
            color = status_colors.get(status, '#6c757d')
            display_text = status.replace('_', ' ').title()
            
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                color,
                display_text
            )
        except Exception as e:
            return f'Error: {str(e)}'
    get_status_display_safe.short_description = 'Status'
    
    def get_queryset(self, request):
        try:
            return super().get_queryset(request).select_related('doctor', 'hospital')
        except:
            return super().get_queryset(request)
    
    def save_model(self, request, obj, form, change):
        try:
            if not obj.appointment_id:
                import uuid
                obj.appointment_id = f"APT-{uuid.uuid4().hex[:8].upper()}"
            
            if not obj.status:
                obj.status = 'scheduled'
            
            if not obj.duration:
                obj.duration = 30
            
            if not obj.consultation_fee:
                obj.consultation_fee = 500.00
            
            super().save_model(request, obj, form, change)
            
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'Error saving appointment: {str(e)}')
    
    def mark_as_confirmed(self, request, queryset):
        try:
            updated = queryset.update(status='confirmed')
            self.message_user(request, f'{updated} appointments marked as confirmed.')
        except Exception as e:
            self.message_user(request, f'Error: {str(e)}', level='ERROR')
    mark_as_confirmed.short_description = "Mark selected appointments as confirmed"
    
    def mark_as_completed(self, request, queryset):
        try:
            updated = queryset.update(status='completed')
            self.message_user(request, f'{updated} appointments marked as completed.')
        except Exception as e:
            self.message_user(request, f'Error: {str(e)}', level='ERROR')
    mark_as_completed.short_description = "Mark selected appointments as completed"
    
    def mark_as_cancelled(self, request, queryset):
        try:
            updated = queryset.update(status='cancelled')
            self.message_user(request, f'{updated} appointments marked as cancelled.')
        except Exception as e:
            self.message_user(request, f'Error: {str(e)}', level='ERROR')
    mark_as_cancelled.short_description = "Mark selected appointments as cancelled"
    
    def mark_as_no_show(self, request, queryset):
        try:
            updated = queryset.update(status='no_show')
            self.message_user(request, f'{updated} appointments marked as no show.')
        except Exception as e:
            self.message_user(request, f'Error: {str(e)}', level='ERROR')
    mark_as_no_show.short_description = "Mark selected appointments as no show"

# Register optional models only if they exist and tables are available
if DOCTORAVAILABILITY_EXISTS:
    try:
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
                try:
                    return obj.get_day_of_week_display()
                except:
                    return 'Error'
            get_day_display.short_description = 'Day'
    except:
        pass

if DOCTORREVIEW_EXISTS:
    try:
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
    except:
        pass

# Custom admin site title
admin.site.site_header = "Hospital Appointment Management"
admin.site.site_title = "Hospital Admin"
admin.site.index_title = "Welcome to Hospital Administration"
