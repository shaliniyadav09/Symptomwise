from django import forms
from django.core.validators import RegexValidator
from .models import HospitalRegistration, HospitalRating

class HospitalRegistrationForm(forms.ModelForm):
    """
    Form for hospital registration
    """
    
    # Additional fields for terms and conditions
    terms_accepted = forms.BooleanField(
        required=True,
        label="I accept the terms and conditions",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    privacy_accepted = forms.BooleanField(
        required=True,
        label="I accept the privacy policy",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = HospitalRegistration
        fields = [
            'hospital_name', 'registration_number', 'license_number',
            'contact_person', 'email', 'phone', 'address', 'city', 
            'state', 'country', 'postal_code', 'preferred_subdomain',
            'license_document', 'registration_document',
            'owner_name', 'owner_email', 'owner_phone', 'owner_designation'
        ]
        
        widgets = {
            'hospital_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter hospital/clinic name'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hospital registration number'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Medical license number'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Primary contact person name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'hospital@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 9876543210'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Complete hospital address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'India'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '123456'
            }),
            'preferred_subdomain': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'yourname',
                'id': 'subdomain-input'
            }),
            'license_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'registration_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'owner_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hospital owner/director name'
            }),
            'owner_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'owner@example.com'
            }),
            'owner_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+91 9876543210'
            }),
            'owner_designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Director, CEO, Owner, etc.'
            }),
        }
        
        labels = {
            'hospital_name': 'Hospital/Clinic Name *',
            'registration_number': 'Registration Number',
            'license_number': 'License Number',
            'contact_person': 'Contact Person *',
            'email': 'Email Address *',
            'phone': 'Phone Number *',
            'address': 'Address *',
            'city': 'City *',
            'state': 'State *',
            'country': 'Country *',
            'postal_code': 'Postal Code *',
            'preferred_subdomain': 'Preferred Subdomain *',
            'license_document': 'License Document',
            'registration_document': 'Registration Document',
            'owner_name': 'Owner/Director Name *',
            'owner_email': 'Owner Email *',
            'owner_phone': 'Owner Phone *',
            'owner_designation': 'Owner Designation *',
        }
        
        help_texts = {
            'preferred_subdomain': 'This will be your hospital\'s web address: yourname.yourdomain.com',
            'license_document': 'Upload medical license (PDF, JPG, PNG - Max 5MB)',
            'registration_document': 'Upload hospital registration certificate (PDF, JPG, PNG - Max 5MB)',
        }
    
    def clean_preferred_subdomain(self):
        subdomain = self.cleaned_data['preferred_subdomain'].lower().strip()
        
        # Check format
        if not subdomain.replace('-', '').replace('_', '').isalnum():
            raise forms.ValidationError(
                'Subdomain can only contain letters, numbers, hyphens, and underscores.'
            )
        
        # Check length
        if len(subdomain) < 3:
            raise forms.ValidationError('Subdomain must be at least 3 characters long.')
        
        if len(subdomain) > 50:
            raise forms.ValidationError('Subdomain cannot be longer than 50 characters.')
        
        # Check for reserved words
        reserved_words = [
            'www', 'api', 'admin', 'app', 'mail', 'ftp', 'blog', 
            'support', 'help', 'docs', 'dev', 'test', 'staging',
            'dashboard', 'login', 'register', 'signup', 'signin'
        ]
        
        if subdomain in reserved_words:
            raise forms.ValidationError('This subdomain is reserved and cannot be used.')
        
        # Check if already exists
        from tenants.models import Hospital
        if Hospital.objects.filter(subdomain=subdomain).exists():
            raise forms.ValidationError('This subdomain is already taken.')
        
        if HospitalRegistration.objects.filter(
            preferred_subdomain=subdomain,
            status__in=['pending', 'approved']
        ).exists():
            raise forms.ValidationError('This subdomain is already requested.')
        
        return subdomain
    
    def clean_email(self):
        email = self.cleaned_data['email']
        
        # Check if email is already registered
        if HospitalRegistration.objects.filter(email=email).exists():
            raise forms.ValidationError('A hospital with this email is already registered.')
        
        return email
    
    def clean_license_document(self):
        file = self.cleaned_data.get('license_document')
        if file:
            # Check file size (5MB limit)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 5MB.')
            
            # Check file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
            if file.content_type not in allowed_types:
                raise forms.ValidationError('Only PDF, JPG, and PNG files are allowed.')
        
        return file
    
    def clean_registration_document(self):
        file = self.cleaned_data.get('registration_document')
        if file:
            # Check file size (5MB limit)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 5MB.')
            
            # Check file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
            if file.content_type not in allowed_types:
                raise forms.ValidationError('Only PDF, JPG, and PNG files are allowed.')
        
        return file

class HospitalRatingForm(forms.ModelForm):
    """
    Form for hospital ratings and reviews
    """
    
    class Meta:
        model = HospitalRating
        fields = [
            'patient_name', 'patient_email', 'overall_rating',
            'cleanliness_rating', 'staff_rating', 'facilities_rating',
            'value_rating', 'review_title', 'review_text',
            'visit_date', 'department', 'treatment_type'
        ]
        
        widgets = {
            'patient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your name'
            }),
            'patient_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com'
            }),
            'overall_rating': forms.Select(attrs={
                'class': 'form-select rating-select'
            }),
            'cleanliness_rating': forms.Select(attrs={
                'class': 'form-select rating-select'
            }),
            'staff_rating': forms.Select(attrs={
                'class': 'form-select rating-select'
            }),
            'facilities_rating': forms.Select(attrs={
                'class': 'form-select rating-select'
            }),
            'value_rating': forms.Select(attrs={
                'class': 'form-select rating-select'
            }),
            'review_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief title for your review'
            }),
            'review_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience...'
            }),
            'visit_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Cardiology, Emergency, etc.'
            }),
            'treatment_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Consultation, Surgery, etc.'
            }),
        }
        
        labels = {
            'patient_name': 'Your Name *',
            'patient_email': 'Email Address',
            'overall_rating': 'Overall Rating *',
            'cleanliness_rating': 'Cleanliness *',
            'staff_rating': 'Staff Behavior *',
            'facilities_rating': 'Facilities *',
            'value_rating': 'Value for Money *',
            'review_title': 'Review Title',
            'review_text': 'Your Review',
            'visit_date': 'Visit Date',
            'department': 'Department Visited',
            'treatment_type': 'Type of Treatment',
        }

class HospitalSearchForm(forms.Form):
    """
    Form for hospital search
    """
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search hospitals...'
        })
    )
    
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    specialty = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Medical specialty'
        })
    )