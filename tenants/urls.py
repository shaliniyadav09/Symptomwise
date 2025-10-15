from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    # Hospital selection and onboarding
    path('select-hospital/', views.select_hospital, name='select_hospital'),
    path('hospital-onboarding/', views.hospital_onboarding, name='hospital_onboarding'),
    path('hospital-setup/<uuid:hospital_id>/', views.hospital_setup, name='hospital_setup'),
    
    # Hospital management
    path('hospital-dashboard/', views.hospital_dashboard, name='hospital_dashboard'),
    path('hospital-settings/<uuid:hospital_id>/', views.hospital_settings, name='hospital_settings'),
    path('hospital-users/<uuid:hospital_id>/', views.hospital_users, name='hospital_users'),
    
    # API endpoints
    path('api/hospital-stats/<uuid:hospital_id>/', views.api_hospital_stats, name='api_hospital_stats'),
]