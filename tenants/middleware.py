from django.http import Http404
from django.shortcuts import get_object_or_404
from .models import Hospital
import threading

# Thread-local storage for current hospital
_thread_locals = threading.local()


def get_current_hospital():
    """Get the current hospital from thread-local storage"""
    return getattr(_thread_locals, 'hospital', None)


def set_current_hospital(hospital):
    """Set the current hospital in thread-local storage"""
    _thread_locals.hospital = hospital


class TenantMiddleware:
    """
    Middleware to detect and set the current tenant (hospital)
    Supports both subdomain and URL parameter detection
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Clear any existing hospital
        set_current_hospital(None)
        
        hospital = None
        
        # Method 1: Detect by subdomain
        host = request.get_host().lower()
        if '.' in host:
            subdomain = host.split('.')[0]
            if subdomain != 'www' and subdomain != 'localhost':
                try:
                    hospital = Hospital.objects.get(subdomain=subdomain, is_active=True)
                except Hospital.DoesNotExist:
                    pass
        
        # Method 2: Detect by URL parameter (for development/testing)
        if not hospital:
            hospital_slug = request.GET.get('hospital') or request.session.get('hospital_slug')
            if hospital_slug:
                try:
                    hospital = Hospital.objects.get(slug=hospital_slug, is_active=True)
                    request.session['hospital_slug'] = hospital_slug
                except Hospital.DoesNotExist:
                    pass
        
        # Method 3: Use default hospital for development
        if not hospital and not request.path.startswith('/admin/'):
            try:
                hospital = Hospital.objects.filter(is_active=True).first()
            except:
                pass
        
        # Set the current hospital
        if hospital:
            set_current_hospital(hospital)
            request.hospital = hospital
        else:
            request.hospital = None
        
        response = self.get_response(request)
        return response


class RequireTenantMiddleware:
    """
    Middleware to ensure a valid tenant is selected for protected views
    """
    
    EXEMPT_PATHS = [
        '/admin/',
        '/accounts/',
        '/hospital-onboarding/',
        '/select-hospital/',
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for exempt paths
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return self.get_response(request)
        
        # Check if hospital is set
        if not hasattr(request, 'hospital') or not request.hospital:
            from django.shortcuts import redirect
            return redirect('select_hospital')
        
        response = self.get_response(request)
        return response