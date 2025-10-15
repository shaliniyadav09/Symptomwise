from django.contrib import admin
from .models import Hospital, HospitalUser


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ['name', 'subdomain', 'city', 'subscription_plan', 'is_active', 'created_at']
    list_filter = ['subscription_plan', 'is_active', 'country', 'created_at']
    search_fields = ['name', 'subdomain', 'email', 'city']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'subdomain', 'email', 'phone', 'website')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Branding', {
            'fields': ('logo', 'primary_color', 'secondary_color')
        }),
        ('Configuration', {
            'fields': ('timezone', 'language', 'currency', 'working_hours')
        }),
        ('Subscription', {
            'fields': ('subscription_plan', 'max_doctors', 'max_appointments_per_month', 'trial_ends_at')
        }),
        ('Features', {
            'fields': ('ai_enabled', 'whatsapp_enabled', 'whatsapp_number', 'payment_gateway_enabled')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'owner', 'created_at', 'updated_at')
        }),
    )


@admin.register(HospitalUser)
class HospitalUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'hospital', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'user__email', 'hospital__name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'hospital')