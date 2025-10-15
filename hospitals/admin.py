from django.contrib import admin
from .models import HospitalFacility, HospitalRegistration, HospitalContact, HospitalService


@admin.register(HospitalFacility)
class HospitalFacilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_hospital_name', 'is_available', 'created_at']
    list_filter = ['is_available', 'created_at']
    search_fields = ['name', 'description']
    
    def get_hospital_name(self, obj):
        try:
            return obj.hospital.name if obj.hospital else 'No Hospital'
        except:
            return 'Error'
    get_hospital_name.short_description = 'Hospital'


@admin.register(HospitalRegistration)
class HospitalRegistrationAdmin(admin.ModelAdmin):
    list_display = ['registration_number', 'get_hospital_name', 'registration_date', 'expiry_date', 'is_active']
    list_filter = ['is_active', 'registration_date']
    search_fields = ['registration_number', 'issuing_authority']
    
    def get_hospital_name(self, obj):
        try:
            return obj.hospital.name if obj.hospital else 'No Hospital'
        except:
            return 'Error'
    get_hospital_name.short_description = 'Hospital'


@admin.register(HospitalContact)
class HospitalContactAdmin(admin.ModelAdmin):
    list_display = ['contact_type', 'contact_value', 'get_hospital_name', 'is_primary', 'is_public']
    list_filter = ['contact_type', 'is_primary', 'is_public']
    search_fields = ['contact_value']
    
    def get_hospital_name(self, obj):
        try:
            return obj.hospital.name if obj.hospital else 'No Hospital'
        except:
            return 'Error'
    get_hospital_name.short_description = 'Hospital'


@admin.register(HospitalService)
class HospitalServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_hospital_name', 'price', 'is_available', 'is_emergency']
    list_filter = ['is_available', 'is_emergency']
    search_fields = ['name', 'description']
    
    def get_hospital_name(self, obj):
        try:
            return obj.hospital.name if obj.hospital else 'No Hospital'
        except:
            return 'Error'
    get_hospital_name.short_description = 'Hospital'
