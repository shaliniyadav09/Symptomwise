from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.conf import settings
from tenants.models import Hospital
from adminapp.models import Doctor, Category, Appointment, MedicalSpecialty
from django.core.exceptions import PermissionDenied
from django.db import connection 
from django.shortcuts import render
from tenants.models import Hospital
from django.core.files.storage import FileSystemStorage
from adminapp.models import Doctor, Category, Appointment, MedicalSpecialty
import uuid                 
import datetime
import traceback


def index(request):
    """
    This view fetches doctors and hospitals for the homepage.
    """
    # Fetch the first 8 available doctors to display on the homepage
    doctors = Doctor.objects.filter(is_available=True)[:8]
    
    # Get counts for the stats display
    doctor_count = Doctor.objects.filter(is_available=True).count()
    hospital_count = Hospital.objects.filter(is_active=True).count()
    
    # Pass the data to the template
    context = {
        'doctors': doctors,
        'doctor_count': doctor_count,
        'hospital_count': hospital_count,
        'total_doctors': doctor_count, # Used for the 'Show More' button logic
    }
    return render(request, 'index.html', context)

# Add this view as well for the 'all_doctors' page to work
def all_doctors(request):
    doctors = Doctor.objects.filter(is_available=True)
    context = {
        'doctors': doctors
    }
    return render(request, 'alldoctors.html', context)



def hospital_required(view_func):
    """Decorator to ensure user owns a hospital"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('hospitals:login')
        try:
            hospital = Hospital.objects.get(owner=request.user)
            request.hospital = hospital  # Add hospital to request
            return view_func(request, *args, **kwargs)
        except Hospital.DoesNotExist:
            messages.error(request, 'No hospital associated with your account.')
            return redirect('hospitals:login')
    return wrapper

def hospital_list(request):
    """List all hospitals"""
    try:
        hospitals = Hospital.objects.filter(is_active=True)
        context = {
            'hospitals': hospitals,
            'hospital_count': hospitals.count()
        }
        return render(request, 'hospitals/list.html', context)
    except Exception as e:
        context = {
            'hospitals': [],
            'hospital_count': 0,
            'error': str(e)
        }
        return render(request, 'hospitals/list.html', context)

def hospital_register(request):
    """Hospital registration"""
    if request.method == 'POST':
        try:
            # Get form data
            hospital_name = request.POST.get('hospital_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            address = request.POST.get('address', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            country = request.POST.get('country', 'India').strip()
            postal_code = request.POST.get('postal_code', '').strip()
            website = request.POST.get('website', '').strip()
            
            # Admin user details
            admin_username = request.POST.get('admin_username', '').strip()
            admin_email = request.POST.get('admin_email', '').strip()
            admin_password = request.POST.get('admin_password', '')
            
            # Validate required fields
            if not all([hospital_name, email, phone, address, city, state, postal_code, admin_username, admin_email, admin_password]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'hospitals/register.html')
            
            # Check if user already exists
            if User.objects.filter(username=admin_username).exists():
                messages.error(request, 'Username already exists. Please choose a different username.')
                return render(request, 'hospitals/register.html')
            
            if User.objects.filter(email=admin_email).exists():
                messages.error(request, 'Email already registered. Please use a different email.')
                return render(request, 'hospitals/register.html')
            
            # Create admin user
            admin_user = User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name=hospital_name,
                is_staff=True  # Give admin privileges
            )
            
            # Generate unique subdomain
            import re
            base_subdomain = re.sub(r'[^a-z0-9]', '', hospital_name.lower())[:15]
            subdomain = base_subdomain
            counter = 1
            
            # Ensure subdomain is unique
            while Hospital.objects.filter(subdomain=subdomain).exists():
                subdomain = f"{base_subdomain}{counter}"
                counter += 1
            
            # Create hospital
            hospital = Hospital.objects.create(
                name=hospital_name,
                slug=hospital_name.lower().replace(' ', '-').replace('_', '-'),
                subdomain=subdomain,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                country=country,
                postal_code=postal_code,
                website=website,
                owner=admin_user,
                is_active=True
            )
            
            # Generate subdomain URL
            domain = request.get_host()
            if 'loca.lt' in domain:
                # For localtunnel, create subdomain URL
                subdomain_url = f'https://{subdomain}.loca.lt'
            elif 'localhost' in domain or '127.0.0.1' in domain:
                # For localhost development
                port = ':8000' if ':8000' not in domain else ''
                subdomain_url = f'http://{subdomain}.localhost{port}'
            else:
                # For production domains
                subdomain_url = f'https://{subdomain}.{domain}'
            
            messages.success(request, f'Hospital "{hospital_name}" registered successfully! You can now login with username: {admin_username}')
            
            # Redirect to login page or success page
            context = {
                'hospital': hospital,
                'admin_username': admin_username,
                'subdomain_url': subdomain_url,
                'success': True
            }
            return render(request, 'hospitals/register_success.html', context)
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'hospitals/register.html')
    
    return render(request, 'hospitals/register.html')

def hospital_login(request):
    """Hospital admin login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if user owns a hospital
            try:
                hospital = Hospital.objects.get(owner=user)
                auth_login(request, user)
                messages.success(request, f'Welcome to {hospital.name} dashboard!')
                return redirect('hospitals:dashboard')
            except Hospital.DoesNotExist:
                messages.error(request, 'No hospital associated with this account.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'hospitals/login.html')

def hospital_logout(request):
    """Hospital admin logout"""
    auth_logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('hospitals:login')

@hospital_required
def hospital_dashboard(request):
    """Hospital dashboard"""
    hospital = request.hospital
    
    # Get hospital statistics
    doctors = Doctor.objects.filter(hospital=hospital)
    appointments = Appointment.objects.filter(hospital=hospital)
    categories = Category.objects.filter(hospital=hospital)
    
    # Recent appointments
    recent_appointments = appointments.order_by('-created_at')[:5]
    
    # Generate subdomain URL
    domain = request.get_host()
    if 'loca.lt' in domain:
        subdomain_url = f'https://{hospital.subdomain}.loca.lt'
    elif 'localhost' in domain or '127.0.0.1' in domain:
        # For localhost development
        port = ':8000' if ':8000' not in domain else ''
        subdomain_url = f'http://{hospital.subdomain}.localhost{port}'
    else:
        # For production domains
        subdomain_url = f'https://{hospital.subdomain}.{domain}'
    
    context = {
        'hospital': hospital,
        'doctors_count': doctors.count(),
        'appointments_count': appointments.count(),
        'categories_count': categories.count(),
        'recent_appointments': recent_appointments,
        'doctors': doctors[:5],  # Show first 5 doctors
        'subdomain_url': subdomain_url,
    }
    return render(request, 'hospitals/dashboard.html', context)

@hospital_required
def hospital_profile(request):
    """Hospital profile management"""
    hospital = request.hospital
    
    if request.method == 'POST':
        # Update hospital details
        hospital.name = request.POST.get('name', hospital.name)
        hospital.email = request.POST.get('email', hospital.email)
        hospital.phone = request.POST.get('phone', hospital.phone)
        hospital.address = request.POST.get('address', hospital.address)
        hospital.city = request.POST.get('city', hospital.city)
        hospital.state = request.POST.get('state', hospital.state)
        hospital.country = request.POST.get('country', hospital.country)
        hospital.postal_code = request.POST.get('postal_code', hospital.postal_code)
        
        hospital.save()
        messages.success(request, 'Hospital profile updated successfully!')
        return redirect('hospitals:profile')
    
    context = {'hospital': hospital}
    return render(request, 'hospitals/profile.html', context)

@hospital_required
def manage_doctor_availability(request, doctor_id):
    """Manage a doctor's weekly availability."""
    hospital = request.hospital
    try:
        doctor = Doctor.objects.get(id=doctor_id, hospital=hospital)
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor not found or you do not have permission to edit this doctor.')
        return redirect('hospitals:doctors')

    # Get the DoctorAvailability model from adminapp
    try:
        from adminapp.models import DoctorAvailability
    except ImportError:
        messages.error(request, 'Availability model not found. Please contact support.')
        return redirect('hospitals:doctors')

    if request.method == 'POST':
        # Clear existing availability for simplicity
        DoctorAvailability.objects.filter(doctor=doctor).delete()

        # Loop through days 0 (Sun) to 6 (Sat)
        for i in range(7):
            day_str = str(i)
            is_active = request.POST.get(f'active_{day_str}')

            if is_active:
                start_time = request.POST.get(f'start_time_{day_str}')
                end_time = request.POST.get(f'end_time_{day_str}')

                if start_time and end_time:
                    DoctorAvailability.objects.create(
                        doctor=doctor,
                        hospital=hospital,
                        day_of_week=i,
                        start_time=start_time,
                        end_time=end_time
                    )
        
        messages.success(request, f"Dr. {doctor.first_name}'s availability has been updated.")
        return redirect('hospitals:doctors')
    
    # GET request: fetch current schedule
    availability = DoctorAvailability.objects.filter(doctor=doctor).order_by('day_of_week')
    
    # Organize schedule into a dictionary for easy access in the template
    schedule = {str(avail.day_of_week): avail for avail in availability}

    days_of_week = [
        (0, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'),
        (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')
    ]

    context = {
        'doctor': doctor,
        'hospital': hospital,
        'schedule': schedule,
        'days_of_week': days_of_week
    }
    return render(request, 'hospitals/manage_availability.html', context)


@hospital_required
def hospital_doctors(request):
    """Manage hospital doctors"""
    hospital = request.hospital
    doctors = Doctor.objects.filter(hospital=hospital)
    
    context = {
        'hospital': hospital,
        'doctors': doctors
    }
    return render(request, 'hospitals/doctors.html', context)

@hospital_required
def hospital_appointments(request):
    """View hospital appointments"""
    hospital = request.hospital
    appointments = Appointment.objects.filter(hospital=hospital).order_by('-appointment_date', '-appointment_time')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    context = {
        'hospital': hospital,
        'appointments': appointments,
        'status_filter': status_filter
    }
    return render(request, 'hospitals/appointments.html', context)

def hospital_detail(request, hospital_id):
    """Hospital detail view with comprehensive information"""
    try:
        hospital = get_object_or_404(Hospital, id=hospital_id, is_active=True)
        doctors = Doctor.objects.filter(hospital=hospital, is_available=True)
        
        # Get hospital statistics
        total_doctors = doctors.count()
        specialties = doctors.values_list('category__name', flat=True).distinct()
        
        # Get recent appointments count (if available)
        try:
            from adminapp.models import Appointment
            recent_appointments = Appointment.objects.filter(hospital=hospital).count()
        except:
            recent_appointments = 0
        
        context = {
            'hospital': hospital,
            'doctors': doctors[:6],  # Show first 6 doctors
            'doctors_count': total_doctors,
            'specialties': list(specialties),
            'specialties_count': len(specialties),
            'recent_appointments': recent_appointments,
            'has_emergency': True,  # All hospitals have emergency services
            'services': [
                'Emergency Services',
                'Laboratory Services', 
                'Pharmacy',
                'General Medicine',
                'Inpatient Care',
                'Ambulance Service',
                'Surgery',
                'Pediatric Care'
            ]
        }
        return render(request, 'hospitals/detail.html', context)
    except Exception as e:
        context = {
            'error': str(e),
            'hospital': None
        }
        return render(request, 'hospitals/detail.html', context)

@hospital_required
def add_category(request):
    """Add new category for hospital"""
    hospital = request.hospital
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            specialty_id = request.POST.get('specialty')
            
            if not name:
                messages.error(request, 'Category name is required.')
                return redirect('hospitals:add_category')
            
            # Check if category already exists for this hospital
            if Category.objects.filter(hospital=hospital, name=name).exists():
                messages.error(request, f'Category "{name}" already exists in your hospital.')
                return redirect('hospitals:add_category')
            
            # Get specialty if selected
            specialty = None
            if specialty_id:
                try:
                    specialty = MedicalSpecialty.objects.get(id=specialty_id)
                except MedicalSpecialty.DoesNotExist:
                    pass
            
            # Create category
            category = Category.objects.create(
                hospital=hospital,
                name=name,
                description=description,
                specialty=specialty
            )
            
            messages.success(request, f'Category "{name}" added successfully!')
            return redirect('hospitals:categories')
            
        except Exception as e:
            messages.error(request, f'Error adding category: {str(e)}')
    
    # Get all medical specialties for dropdown
    specialties = MedicalSpecialty.objects.filter(is_active=True)
    
    context = {
        'hospital': hospital,
        'specialties': specialties
    }
    return render(request, 'hospitals/add_category.html', context)

@hospital_required
def add_doctor(request):
    """
    Add new doctor using Django's ORM for safety, reliability, and correct ID formatting.
    """
    hospital = request.hospital
    
    if request.method == 'POST':
        try:
            # --- 1. Data Retrieval & Validation ---
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            title = request.POST.get('title', 'Dr.')
            category_id = request.POST.get('category')
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            experience_years = request.POST.get('experience_years', '5')
            education = request.POST.get('education', '').strip()
            professional_bio_from_form = request.POST.get('bio', '').strip()
            consultation_fee = request.POST.get('consultation_fee', '500')
            languages = request.POST.get('languages', 'English').strip()
            license_number = request.POST.get('license_number', '').strip()

            if not all([first_name, last_name, category_id]):
                messages.error(request, 'First name, last name, and category are required.')
                return redirect('hospitals:add_doctor')

            category = Category.objects.get(id=category_id, hospital=hospital)
            is_available = request.POST.get('is_available', '1') == '1'

            # --- 2. Handle the Image Upload ---
            image_db_path = None
            profile_image_file = request.FILES.get('profile_image')
            if profile_image_file:
                fs = FileSystemStorage()
                # Saves the file and returns its path relative to MEDIA_ROOT
                filename = fs.save(f"doctor_profiles/{profile_image_file.name}", profile_image_file)
                image_db_path = filename

            # --- 3. Create the Doctor object using the Django ORM ---
            # This is safer and automatically handles all relationships and data types.
            Doctor.objects.create(
                # CRITICAL FIX: Save the hospital_id without hyphens to match the database standard.
                hospital_id=hospital.id.hex, 
                
                first_name=first_name,
                last_name=last_name,
                title=title,
                category=category,
                email=email,
                phone=phone,
                experience_years=int(experience_years) if experience_years else 5,
                education=education,
                description=professional_bio_from_form, # Maps the form's "bio" to the description field
                bio=category.name, # Sets the "bio" field to the category name
                consultation_fee=float(consultation_fee) if consultation_fee else 500.0,
                languages=languages,
                license_number=license_number,
                is_available=is_available,
                profile_image=image_db_path # Assigns the path of the saved image
            )
            
            messages.success(request, f'Dr. {first_name} {last_name} has been added successfully!')
            return redirect('hospitals:doctors')

        except Exception as e:
            # This will catch any error during the process and show a helpful message.
            messages.error(request, f'Error adding doctor: {str(e)}')
            return redirect('hospitals:add_doctor')

    # This part handles the GET request (when you first load the page)
    categories = Category.objects.filter(hospital=hospital, is_active=True)
    context = {
        'hospital': hospital,
        'categories': categories
    }
    return render(request, 'hospitals/add_doctor.html', context)

def forgot_password(request):
    """Forgot password view"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'hospitals/forgot_password.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user owns a hospital
            try:
                hospital = Hospital.objects.get(owner=user)
            except Hospital.DoesNotExist:
                messages.error(request, 'No hospital account found with this email address.')
                return render(request, 'hospitals/forgot_password.html')
            
            # Generate password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link with proper domain
            domain = request.get_host()
            if 'loca.lt' in domain:
                reset_link = f'https://{domain}/hospitals/reset-password/{uid}/{token}/'
            elif 'localhost' in domain or '127.0.0.1' in domain:
                reset_link = f'http://{domain}/hospitals/reset-password/{uid}/{token}/'
            else:
                reset_link = request.build_absolute_uri(
                    f'/hospitals/reset-password/{uid}/{token}/'
                )
            
            # Send email
            subject = 'Password Reset - Hospital Admin'
            message = f"""Hello {user.first_name or user.username},

You requested a password reset for your hospital admin account.

Hospital: {hospital.name}
Username: {user.username}

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

If you didn't request this reset, please ignore this email.

Best regards,
SymptomWise Team"""
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, f'Password reset link has been sent to {email}. Please check your inbox.')
            return redirect('hospitals:login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return render(request, 'hospitals/forgot_password.html')
        except Exception as e:
            messages.error(request, 'Error sending email. Please try again later.')
            return render(request, 'hospitals/forgot_password.html')
    
    return render(request, 'hospitals/forgot_password.html')

def reset_password(request, uidb64, token):
    """Password reset view"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not new_password or not confirm_password:
                messages.error(request, 'Please fill in both password fields.')
                return render(request, 'hospitals/reset_password.html', {'valid_link': True})
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'hospitals/reset_password.html', {'valid_link': True})
            
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'hospitals/reset_password.html', {'valid_link': True})
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            messages.success(request, 'Your password has been reset successfully. You can now login with your new password.')
            return redirect('hospitals:login')
        
        return render(request, 'hospitals/reset_password.html', {'valid_link': True})
    else:
        return render(request, 'hospitals/reset_password.html', {'valid_link': False})

@hospital_required
def categories(request):
    """List hospital categories"""
    hospital = request.hospital
    categories = Category.objects.filter(hospital=hospital)
    
    context = {
        'hospital': hospital,
        'categories': categories
    }
    return render(request, 'hospitals/categories.html', context)

@hospital_required
def edit_doctor(request, doctor_id):
    """
    Handles editing doctor details, including profile image uploads.
    """
    hospital = request.hospital
    doctor = get_object_or_404(Doctor, id=doctor_id, hospital=hospital)

    if request.method == 'POST':
        try:
            # Update all text-based fields from the form
            doctor.first_name = request.POST.get('first_name', doctor.first_name).strip()
            doctor.last_name = request.POST.get('last_name', doctor.last_name).strip()
            doctor.title = request.POST.get('title', doctor.title)
            doctor.email = request.POST.get('email', doctor.email).strip()
            doctor.phone = request.POST.get('phone', doctor.phone).strip()
            doctor.experience_years = int(request.POST.get('experience_years', doctor.experience_years))
            doctor.education = request.POST.get('education', doctor.education).strip()
            doctor.bio = request.POST.get('bio', doctor.bio).strip()
            # Also update the 'description' field if it's in your form
            doctor.description = request.POST.get('description', doctor.description).strip()
            doctor.consultation_fee = float(request.POST.get('consultation_fee', doctor.consultation_fee))
            doctor.languages = request.POST.get('languages', doctor.languages).strip()
            doctor.license_number = request.POST.get('license_number', doctor.license_number).strip()
            doctor.is_available = request.POST.get('is_available') == '1'
            
            # --- THIS IS THE CRUCIAL PART FOR HANDLING THE IMAGE ---
            # Check if a new image file was uploaded in the form
            if request.FILES.get('profile_image'):
                image_file = request.FILES['profile_image']
                fs = FileSystemStorage()
                
                # Optional but recommended: Delete the old image file to prevent clutter
                if doctor.profile_image and hasattr(doctor.profile_image, 'name'):
                    fs.delete(doctor.profile_image.name)
                    
                # Save the new file to 'media/doctor_profiles/' and get its path
                filename = fs.save(f"doctor_profiles/{image_file.name}", image_file)
                doctor.profile_image = filename # Update the doctor's image path in the model

            # Update the category relationship
            category_id = request.POST.get('category')
            if category_id:
                doctor.category = get_object_or_404(Category, id=category_id, hospital=hospital)
            
            # Save all the changes (both text and image path) to the database
            doctor.save()
            
            messages.success(request, f'Dr. {doctor.full_name} has been updated successfully!')
            return redirect('hospitals:doctors')
            
        except Exception as e:
            messages.error(request, f'Error updating doctor: {str(e)}')
    
    # This part handles the GET request (when you first load the page)
    categories = Category.objects.filter(hospital=hospital, is_active=True)
    context = {
        'hospital': hospital,
        'doctor': doctor,
        'categories': categories
    }
    return render(request, 'hospitals/edit_doctor.html', context)

@hospital_required
def delete_doctor(request, doctor_id):
    """Delete doctor safely with direct database handling"""
    hospital = request.hospital
    
    try:
        # Get the doctor with proper error handling
        doctor = get_object_or_404(Doctor, id=doctor_id, hospital=hospital)
        doctor_name = f"Dr. {doctor.first_name} {doctor.last_name}"
        
        # Use direct database operations to avoid any ORM issues
        from django.db import connection, transaction
        
        with transaction.atomic():
            with connection.cursor() as cursor:
                try:
                    # First, clean up any references to old tables in the database
                    # Check and drop any problematic triggers
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND sql LIKE '%doctor_old%'")
                    bad_triggers = cursor.fetchall()
                    for trigger in bad_triggers:
                        cursor.execute(f"DROP TRIGGER IF EXISTS {trigger[0]}")
                    
                    # Delete related records using correct table names
                    cursor.execute("DELETE FROM adminapp_doctoravailability WHERE doctor_id = %s", [doctor_id])
                    cursor.execute("UPDATE adminapp_appointment SET doctor_id = NULL WHERE doctor_id = %s", [doctor_id])
                    
                    # Try to delete doctor reviews if table exists
                    try:
                        cursor.execute("DELETE FROM adminapp_doctorreview WHERE doctor_id = %s", [doctor_id])
                    except Exception:
                        pass  # Table might not exist
                    
                    # Finally delete the doctor
                    cursor.execute("DELETE FROM adminapp_doctor WHERE id = %s", [doctor_id])
                    
                    if cursor.rowcount == 0:
                        raise Exception("Doctor not found or already deleted")
                    
                except Exception as db_error:
                    # If direct SQL fails, try Django ORM as fallback
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Direct SQL failed for doctor {doctor_id}: {str(db_error)}, trying ORM")
                    
                    # Rollback the transaction and try ORM
                    raise db_error
        
        messages.success(request, f'{doctor_name} has been removed from your hospital.')
        
    except Doctor.DoesNotExist:
        messages.error(request, 'Doctor not found or access denied.')
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting doctor {doctor_id}: {str(e)}")
        
        # Try alternative deletion method
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                # Force delete with minimal dependencies
                cursor.execute("PRAGMA foreign_keys = OFF")
                cursor.execute("DELETE FROM adminapp_doctor WHERE id = %s", [doctor_id])
                cursor.execute("PRAGMA foreign_keys = ON")
                
                if cursor.rowcount > 0:
                    messages.success(request, f'Doctor has been removed (forced deletion).')
                else:
                    messages.error(request, 'Doctor not found.')
        except Exception as final_error:
            messages.error(request, f'Error deleting doctor: {str(final_error)}')
    
    return redirect('hospitals:doctors')
