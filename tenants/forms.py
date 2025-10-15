from django import forms
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from .models import Hospital


class HospitalOnboardingForm(forms.ModelForm):
    """
    Form for hospital registration and onboarding
    """
    
    # Admin user fields
    admin_first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    admin_last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    admin_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'admin@hospital.com'})
    )
    admin_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    admin_password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    
    # Terms and conditions
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Hospital
        fields = [
            'name', 'subdomain', 'email', 'phone', 'address', 
            'city', 'state', 'country', 'postal_code', 'website',
            'timezone', 'language', 'currency'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apollo Hospital'}),
            'subdomain': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'apollo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'info@hospital.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Hospital Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mumbai'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Maharashtra'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'value': 'India'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '400001'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://hospital.com'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Timezone choices
        self.fields['timezone'].choices = [
            ('Asia/Kolkata', 'India Standard Time (IST)'),
            ('Asia/Dubai', 'Gulf Standard Time (GST)'),
            ('America/New_York', 'Eastern Time (ET)'),
            ('Europe/London', 'Greenwich Mean Time (GMT)'),
            ('Asia/Singapore', 'Singapore Standard Time (SGT)'),
        ]
        
        # Language choices
        self.fields['language'].choices = [
            ('en', 'English'),
            ('hi', 'Hindi'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('ar', 'Arabic'),
        ]
        
        # Currency choices
        self.fields['currency'].choices = [
            ('INR', 'Indian Rupee (₹)'),
            ('USD', 'US Dollar ($)'),
            ('EUR', 'Euro (€)'),
            ('GBP', 'British Pound (£)'),
            ('AED', 'UAE Dirham (د.إ)'),
        ]
    
    def clean_subdomain(self):
        subdomain = self.cleaned_data['subdomain'].lower()
        
        # Check if subdomain is available
        if Hospital.objects.filter(subdomain=subdomain).exists():
            raise forms.ValidationError('This subdomain is already taken')
        
        # Reserved subdomains
        reserved = ['www', 'admin', 'api', 'app', 'mail', 'ftp', 'localhost']
        if subdomain in reserved:
            raise forms.ValidationError('This subdomain is reserved')
        
        return subdomain
    
    def clean_admin_email(self):
        email = self.cleaned_data['admin_email']
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError('A user with this email already exists')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('admin_password')
        password_confirm = cleaned_data.get('admin_password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match')
        
        return cleaned_data


class HospitalConfigForm(forms.ModelForm):
    """
    Form for hospital configuration and settings
    """
    
    class Meta:
        model = Hospital
        fields = [
            'name', 'email', 'phone', 'address', 'city', 'state', 'country', 'postal_code',
            'website', 'logo', 'primary_color', 'secondary_color', 'timezone', 'language', 'currency',
            'working_hours', 'ai_enabled', 'whatsapp_enabled', 'whatsapp_number',
            'payment_gateway_enabled', 'smtp_host', 'smtp_port', 'smtp_username', 'smtp_use_tls'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'working_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'JSON format: {"monday": {"start": "09:00", "end": "17:00"}, ...}'}),
            'ai_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'whatsapp_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 9876543210'}),
            'payment_gateway_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'smtp_host': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'smtp.gmail.com'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '587'}),
            'smtp_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'email@gmail.com'}),
            'smtp_use_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Same choices as onboarding form
        self.fields['timezone'].choices = [
            ('Asia/Kolkata', 'India Standard Time (IST)'),
            ('Asia/Dubai', 'Gulf Standard Time (GST)'),
            ('America/New_York', 'Eastern Time (ET)'),
            ('Europe/London', 'Greenwich Mean Time (GMT)'),
            ('Asia/Singapore', 'Singapore Standard Time (SGT)'),
        ]
        
        self.fields['language'].choices = [
            ('en', 'English'),
            ('hi', 'Hindi'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('ar', 'Arabic'),
        ]
        
        self.fields['currency'].choices = [
            ('INR', 'Indian Rupee (₹)'),
            ('USD', 'US Dollar ($)'),
            ('EUR', 'Euro (€)'),
            ('GBP', 'British Pound (£)'),
            ('AED', 'UAE Dirham (د.إ)'),
        ]