from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from tenants.models import Hospital
from adminapp.models import Doctor, DoctorAvailability
import json

def index(request):
    """Completely fixed home page - no problematic field access"""
    try:
        # Get hospitals safely
        hospitals = Hospital.objects.filter(is_active=True)[:5]
        
        # Get doctors with minimal field access to avoid errors
        doctors = Doctor.objects.filter(is_available=True)[:8]
        
        # Build safe context
        context = {
            'hospitals': hospitals,
            'doctors': doctors,
            'hospital_count': hospitals.count(),
            'doctor_count': doctors.count(),
            'total_doctors': Doctor.objects.filter(is_available=True).count(),
        }
        
        return render(request, 'index.html', context)
        
    except Exception as e:
        # Ultimate fallback
        print(f"Homepage error: {e}")
        context = {
            'error': str(e),
            'hospitals': [],
            'doctors': [],
            'hospital_count': 0,
            'doctor_count': 0,
            'total_doctors': 0,
        }
        return render(request, 'index.html', context)

def about(request):
    """About page"""
    return render(request, 'about.html', {'title': 'About Us'})

def contact(request):
    """Contact page with email functionality"""
    if request.method == 'POST':
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            # Get form data
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()
            
            # Validate required fields
            if not all([first_name, last_name, email, subject, message]):
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'contact.html', {'title': 'Contact Us'})
            
            # Prepare email content
            email_subject = f'Contact Form: {subject}'
            email_message = f"""New contact form submission from SymptomWise website:

Name: {first_name} {last_name}
Email: {email}
Phone: {phone}
Subject: {subject}

Message:
{message}

---
This message was sent from the SymptomWise contact form.
"""
            
            # Send email using EmailMessage for better control
            from django.core.mail import EmailMessage
            
            email_msg = EmailMessage(
                email_subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                ['symptomwiseprivatelimited@gmail.com'],
                reply_to=[email],
            )
            email_msg.send()
            
            # Send confirmation email to user
            confirmation_subject = 'Thank you for contacting SymptomWise'
            confirmation_message = f"""Dear {first_name},

Thank you for contacting SymptomWise. We have received your message and will get back to you within 24 hours.

Your message:
Subject: {subject}
Message: {message}

If you have any urgent medical concerns, please call 108 for emergency services.

Best regards,
SymptomWise Team
"""
            
            send_mail(
                confirmation_subject,
                confirmation_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,  # Don't fail if confirmation email fails
            )
            
            messages.success(request, f'Thank you {first_name}! Your message has been sent successfully. We will get back to you soon.')
            return redirect('contact')
            
        except Exception as e:
            print(f"Contact form error: {str(e)}")  # Debug print
            messages.error(request, f'Sorry, there was an error sending your message. Please try again or contact us directly at symptomwiseprivatelimited@gmail.com')
            return render(request, 'contact.html', {'title': 'Contact Us'})
    
    return render(request, 'contact.html', {'title': 'Contact Us'})

def services(request):
    """Services page"""
    return render(request, 'services.html', {'title': 'Our Services'})

def adminlogin(request):
    """Admin login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            auth_login(request, user)
            return redirect('/admin/')
        else:
            messages.error(request, 'Invalid credentials or not an admin user')
    
    return render(request, 'adminlogin.html')

def adminlog(request):
    """Admin logout"""
    auth_logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('/')

def register(request):
    """User registration with enhanced validation"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validate required fields
        if not all([username, email, password, confirm_password]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'register.html')
        
        # Validate password match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')
        
        # Validate username format
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
            messages.error(request, 'Username must start with a letter and contain only letters, numbers, underscore, and hyphen')
            return render(request, 'register.html')
        
        # Validate password strength
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request, 'register.html')
        
        if not re.search(r'[A-Z]', password):
            messages.error(request, 'Password must contain at least one uppercase letter')
            return render(request, 'register.html')
        
        if not re.search(r'[a-z]', password):
            messages.error(request, 'Password must contain at least one lowercase letter')
            return render(request, 'register.html')
        
        if not re.search(r'\d', password):
            messages.error(request, 'Password must contain at least one number')
            return render(request, 'register.html')
        
        if not re.search(r'[^a-zA-Z\d]', password):
            messages.error(request, 'Password must contain at least one special character')
            return render(request, 'register.html')
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose a different username.')
            return render(request, 'register.html')
        
        # Check if email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered. Please use a different email or try logging in.')
            return render(request, 'register.html')
        
        try:
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            
            messages.success(request, f'Registration successful! Welcome {username}. Please login with your credentials.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            print(f"Registration error: {str(e)}")  # Debug print
    
    return render(request, 'register.html')

def login(request):
    """User login with enhanced debugging and validation"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Debug logging
        print(f"Login attempt - Username: '{username}', Password length: {len(password)}")
        
        # Validate input
        if not username or not password:
            messages.error(request, 'Please enter both username and password')
            return render(request, 'login.html')
        
        # Validate username format
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', username):
            messages.error(request, 'Invalid username format. Username must start with a letter and contain only letters, numbers, underscore, and hyphen.')
            return render(request, 'login.html')
        
        # Try authentication
        user = authenticate(request, username=username, password=password)
        print(f"Authentication result: {user}")
        
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                
                # Redirect to next page if specified, otherwise to home
                next_page = request.GET.get('next', '/')
                return redirect(next_page)
            else:
                messages.error(request, 'Your account has been deactivated. Please contact support.')
        else:
            # Check if user exists to provide better error message
            try:
                existing_user = User.objects.get(username=username)
                messages.error(request, 'Invalid password. Please check your password and try again.')
                print(f"User exists but password incorrect for: {username}")
            except User.DoesNotExist:
                messages.error(request, 'Username not found. Please check your username or register for a new account.')
                print(f"User does not exist: {username}")
    
    return render(request, 'login.html')

def logout(request):
    """User logout"""
    username = request.user.username if request.user.is_authenticated else 'User'
    auth_logout(request)
    messages.success(request, f'Goodbye {username}! You have been logged out successfully.')
    return redirect('/')

def userdashboard(request):
    """User dashboard with user appointments - redirects hospital owners to hospital dashboard"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Check if user owns a hospital - if so, redirect to hospital dashboard
    try:
        hospital = Hospital.objects.get(owner=request.user)
        return redirect('hospitals:dashboard')
    except Hospital.DoesNotExist:
        pass  # User is not a hospital owner, continue to user dashboard
    
    # Get user's appointments
    from adminapp.models import Appointment
    user_appointments = Appointment.objects.filter(
        email=request.user.email
    ).order_by('-appointment_date', '-appointment_time')[:5]
    
    context = {
        'user': request.user,
        'hospitals': Hospital.objects.all()[:5],
        'doctors': Doctor.objects.all()[:5],
        'appointments': user_appointments,
        'appointments_count': user_appointments.count(),
    }
    return render(request, 'userdashboard.html', context)

def userprofile(request):
    """User profile"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        messages.success(request, 'Profile updated successfully!')
    
    return render(request, 'userprofile.html', {'user': request.user})

def appointment(request):
    """Enhanced appointment booking with hospital/doctor pre-selection and doctor cards"""
    hospitals = Hospital.objects.filter(is_active=True)
    
    # Check if hospital is pre-selected
    selected_hospital_id = request.GET.get('hospital')
    selected_doctor_id = request.GET.get('doctor')
    selected_doctor = None
    selected_hospital = None
    doctors = Doctor.objects.filter(is_available=True)
    hospital_doctors = []
    
    # Handle hospital pre-selection
    if selected_hospital_id:
        try:
            selected_hospital = Hospital.objects.get(id=selected_hospital_id, is_active=True)
            # Get doctors from the selected hospital for cards display
            hospital_doctors = Doctor.objects.filter(hospital=selected_hospital, is_available=True)
            # Filter doctors to only show those from the selected hospital
            doctors = hospital_doctors
        except Hospital.DoesNotExist:
            messages.warning(request, 'Selected hospital not found.')
    
    # Handle doctor pre-selection (takes priority over hospital)
    if selected_doctor_id:
        try:
            selected_doctor = Doctor.objects.get(id=selected_doctor_id, is_available=True)
            selected_hospital = selected_doctor.hospital
            # Get all doctors from the doctor's hospital for cards display
            hospital_doctors = Doctor.objects.filter(hospital=selected_hospital, is_available=True)
            # Filter doctors to only show those from the doctor's hospital
            doctors = hospital_doctors
        except Doctor.DoesNotExist:
            messages.warning(request, 'Selected doctor not found.')
    
    context = {
        'doctors': doctors,
        'hospitals': hospitals,
        'selected_doctor': selected_doctor,
        'selected_hospital': selected_hospital,
        'hospital_doctors': hospital_doctors,  # For displaying doctor cards
        'show_doctor_cards': bool(selected_hospital),  # Show cards if hospital is selected
    }
    return render(request, 'appointment.html', context)

def bookappointment(request):
    """Book appointment with all required fields and send confirmation email"""
    if request.method == 'POST':
        try:
            from adminapp.models import Appointment
            from tenants.models import Hospital
            from .email_utils import send_appointment_confirmation_email
            import uuid
            
            # Get form data
            hospital_id = request.POST.get('hospital')
            doctor_id = request.POST.get('doctor')
            date = request.POST.get('date')
            time = request.POST.get('time')
            reason = request.POST.get('reason', '')
            
            # Get patient information
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()
            date_of_birth = request.POST.get('date_of_birth', '')
            gender = request.POST.get('gender', '')
            zipcode = request.POST.get('zipcode', '').strip()
            address = request.POST.get('address', '').strip()
            
            # Validate required fields
            if not all([hospital_id, doctor_id, date, time, first_name, last_name, phone, email, date_of_birth, gender, zipcode]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('appointment')
            
            # Get the doctor and hospital
            doctor = Doctor.objects.get(id=doctor_id)
            hospital = Hospital.objects.get(id=hospital_id)
            
            # Get consultation fee
            consultation_fee = doctor.consultation_fee if hasattr(doctor, 'consultation_fee') else 500.00
            
            # Create appointment using Django ORM (more reliable than raw SQL)
            appointment = Appointment.objects.create(
                doctor=doctor,
                hospital=hospital,
                patient_user=request.user if request.user.is_authenticated else None,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email=email,
                date_of_birth=date_of_birth,
                gender=gender,
                address=address,
                zipcode=zipcode,
                appointment_date=date,
                appointment_time=time,
                reason=reason,
                consultation_fee=consultation_fee,
                status='scheduled',
                duration=30,
                is_paid=False
            )
            
            # Prepare email data
            email_data = {
                'appointment_id': appointment.appointment_id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'doctor_name': doctor.full_name,
                'hospital_name': hospital.name,
                'appointment_date': date,
                'appointment_time': time,
                'consultation_fee': consultation_fee
            }
            
            # Send confirmation email
            try:
                email_sent = send_appointment_confirmation_email(email_data)
            except Exception as email_error:
                print(f"Email sending failed: {str(email_error)}")
                # Don't fail the appointment booking if email fails
            
            # Redirect to confirmation page with appointment details
            return redirect('appointment_confirmation', appointment_id=appointment.appointment_id)
            
        except Exception as e:
            messages.error(request, f'Error booking appointment: {str(e)}')
            print(f"Appointment booking error: {str(e)}")  # Debug print
            return redirect('appointment')
    
    return redirect('appointment')

def viewappointment(request):
    """View all user appointments"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    from adminapp.models import Appointment
    appointments = Appointment.objects.filter(
        email=request.user.email
    ).order_by('-appointment_date', '-appointment_time')
    
    context = {
        'appointments': appointments,
        'user': request.user,
    }
    return render(request, 'viewappointment.html', context)

def cancel_appointment(request, appointment_id):
    """Cancel appointment"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        from adminapp.models import Appointment
        appointment = Appointment.objects.get(
            appointment_id=appointment_id,
            email=request.user.email
        )
        
        if appointment.status in ['scheduled', 'confirmed']:
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, f'Appointment {appointment_id} has been cancelled successfully!')
        else:
            messages.error(request, 'This appointment cannot be cancelled.')
            
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found or access denied.')
    
    return redirect('userdashboard')

def cancel_appointment_page(request, appointment_id):
    """Cancel appointment confirmation page"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        from adminapp.models import Appointment
        appointment = Appointment.objects.get(
            appointment_id=appointment_id,
            email=request.user.email
        )
        
        if request.method == 'POST':
            if appointment.status in ['scheduled', 'confirmed']:
                appointment.status = 'cancelled'
                appointment.save()
                messages.success(request, f'Appointment {appointment_id} has been cancelled successfully!')
                return redirect('userdashboard')
            else:
                messages.error(request, 'This appointment cannot be cancelled.')
        
        context = {
            'appointment': appointment,
            'user': request.user,
        }
        return render(request, 'cancel_appointment.html', context)
        
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found or access denied.')
        return redirect('userdashboard')

# API endpoints for AJAX calls
@csrf_exempt
def get_doctors_by_hospital(request):
    """Get doctors by hospital (AJAX endpoint) - Fixed to avoid database errors and include images"""
    if request.method == 'POST':
        hospital_id = request.POST.get('hospital_id')
        try:
            doctors = Doctor.objects.filter(hospital_id=hospital_id, is_available=True)
            doctor_list = []
            
            for d in doctors:
                try:
                    # Safe field access to avoid database errors
                    doctor_name = f"{d.title} {d.first_name} {d.last_name}"
                    specialty = d.category.name if d.category else 'General Medicine'
                    
                    # Handle doctor image
                    doctor_image = None
                    if hasattr(d, 'profile_image') and d.profile_image:
                        try:
                            doctor_image = d.profile_image.url
                        except:
                            doctor_image = None
                    
                    doctor_data = {
                        'id': d.id,
                        'name': doctor_name,
                        'specialty': specialty,
                        'experience': d.experience_years,
                        'fee': str(d.consultation_fee) if d.consultation_fee else '500',
                        'image': doctor_image
                    }
                    doctor_list.append(doctor_data)
                except Exception as e:
                    # Skip this doctor if there's an error
                    print(f"Error processing doctor {d.id}: {e}")
                    continue
            
            return JsonResponse({'doctors': doctor_list})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request'})

@csrf_exempt
def search_doctors(request):
    """Search doctors (AJAX endpoint)"""
    if request.method == 'POST':
        search_term = request.POST.get('search', '')
        try:
            doctors = Doctor.objects.filter(title__icontains=search_term)
            doctor_list = [{'id': d.id, 'name': f'Dr. {d.title}'} for d in doctors]
            return JsonResponse({'doctors': doctor_list})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request'})

@csrf_exempt
def get_hospital_info(request):
    """Get hospital information (AJAX endpoint)"""
    if request.method == 'POST':
        hospital_id = request.POST.get('hospital_id')
        try:
            hospital = Hospital.objects.get(id=hospital_id, is_active=True)
            hospital_info = {
                'id': hospital.id,
                'name': hospital.name,
                'address': hospital.address,
                'city': hospital.city,
                'state': hospital.state,
                'phone': hospital.phone,
                'email': hospital.email
            }
            return JsonResponse({'hospital': hospital_info})
        except Hospital.DoesNotExist:
            return JsonResponse({'error': 'Hospital not found'})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request'})


def userdash(request):
    """User dashboard (alias for userdashboard)"""
    return userdashboard(request)

def doctor_list(request, id):
    """
    Doctor detail page - Corrected to work with the new database schema.
    """
    try:
        doctor = get_object_or_404(Doctor, id=id)

        # Fetch the new availability schedule
        availability = DoctorAvailability.objects.filter(doctor=doctor, is_active=True).order_by('day_of_week', 'start_time')

        context = {
            'doctor': doctor,
            'availability': availability, # Pass the new schedule to the template
            'title': f'Profile of {doctor.full_name}'
        }
        return render(request, 'doctor_detail.html', context)

    except Exception as e:
        messages.error(request, f"Could not load doctor profile: {e}")
        return redirect('index')

def book_appointment(request):
    """Book appointment (alias for appointment)"""
    return appointment(request)

def appointment_confirmation(request, appointment_id):
    """Appointment confirmation page with details"""
    try:
        from adminapp.models import Appointment
        appointment = Appointment.objects.get(appointment_id=appointment_id)
        
        context = {
            'appointment': appointment,
            'success': True,
            'message': 'Your appointment has been booked successfully!'
        }
    except Appointment.DoesNotExist:
        context = {
            'appointment': None,
            'success': False,
            'message': 'Appointment not found.'
        }
    
    return render(request, 'appointment_confirmation.html', context)

def get_available_slots(request):
    """Get available appointment slots (AJAX endpoint)"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        date = request.POST.get('date')
        
        # Mock available slots - replace with actual logic
        slots = [
            '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
            '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'
        ]
        
        return JsonResponse({'slots': slots})
    
    return JsonResponse({'error': 'Invalid request'})

def system_status(request):
    """System status dashboard"""
    return render(request, 'system_status.html', {
        'title': 'System Status Dashboard'
    })

def all_doctors(request):
    """Show all doctors page with safe queries"""
    try:
        # Get all doctors safely
        doctors = Doctor.objects.filter(is_available=True)
        selected_hospital = None
        
        # Get all hospitals for filter dropdown
        hospitals = Hospital.objects.filter(is_active=True)
        
        # Get all specialties for filter dropdown
        from adminapp.models import MedicalSpecialty
        specialties = MedicalSpecialty.objects.filter(is_active=True)
        
        # Check if hospital filter is applied
        hospital_id = request.GET.get('hospital')
        if hospital_id:
            try:
                selected_hospital = Hospital.objects.get(id=hospital_id)
                doctors = doctors.filter(hospital=selected_hospital)
            except Hospital.DoesNotExist:
                messages.warning(request, 'Selected hospital not found.')
        
        # Check if specialty filter is applied
        specialty_id = request.GET.get('specialty')
        if specialty_id:
            try:
                specialty = MedicalSpecialty.objects.get(id=specialty_id)
                doctors = doctors.filter(specialty=specialty)
            except MedicalSpecialty.DoesNotExist:
                messages.warning(request, 'Selected specialty not found.')
        
        # Order by doctor name (avoid hospital__ joins that might cause issues)
        doctors = doctors.order_by('last_name', 'first_name')
        
        context = {
            'doctors': doctors,
            'hospitals': hospitals,
            'specialties': specialties,
            'title': f'All Doctors{" at " + selected_hospital.name if selected_hospital else ""}',
            'total_doctors': doctors.count(),
            'selected_hospital': selected_hospital,
        }
        return render(request, 'alldoctors.html', context)
    except Exception as e:
        messages.error(request, f'Error loading doctors: {str(e)}')
        return redirect('index')

def password_reset_request(request):
    """Password reset request view"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'registration/password_reset_form.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset link with proper domain
            domain = request.get_host()
            if 'loca.lt' in domain:
                reset_link = f'https://{domain}/password-reset-confirm/{uid}/{token}/'
            elif 'localhost' in domain or '127.0.0.1' in domain:
                reset_link = f'http://{domain}/password-reset-confirm/{uid}/{token}/'
            else:
                reset_link = request.build_absolute_uri(
                    f'/password-reset-confirm/{uid}/{token}/'
                )
            
            # Send email
            subject = 'Password Reset - SymptomWise'
            message = f"""Hello {user.first_name or user.username},

You have requested to reset your password for your SymptomWise account.

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Best regards,
SymptomWise Team
"""
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'registration/password_reset_form.html')

def password_reset_confirm(request, uidb64, token):
    """Password reset confirmation view"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('new_password1')
            password2 = request.POST.get('new_password2')
            
            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
            elif len(password1) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
            else:
                user.set_password(password1)
                user.save()
                messages.success(request, 'Your password has been reset successfully. You can now log in.')
                return redirect('login')
        
        return render(request, 'registration/password_reset_confirm.html', {
            'validlink': True,
            'user': user
        })
    else:
        return render(request, 'registration/password_reset_confirm.html', {
            'validlink': False
        })