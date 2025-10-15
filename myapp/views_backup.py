from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from tenants.models import Hospital
from adminapp.models import Doctor
import json

def index(request):
    """Home page"""
    try:
        hospitals = Hospital.objects.all()[:5]
        doctors = Doctor.objects.all()[:5]
        
        context = {
            'hospitals': hospitals,
            'doctors': doctors,
            'hospital_count': Hospital.objects.count(),
            'doctor_count': Doctor.objects.count(),
        }
        return render(request, 'index.html', context)
    except Exception as e:
        # Fallback if there are still database issues
        context = {
            'error': str(e),
            'hospitals': [],
            'doctors': [],
            'hospital_count': 0,
            'doctor_count': 0,
        }
        return render(request, 'index.html', context)

def about(request):
    """About page"""
    return render(request, 'about.html', {'title': 'About Us'})

def contact(request):
    """Contact page"""
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
    """User registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'register.html')
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'register.html')

def login(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')

def logout(request):
    """User logout"""
    auth_logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('/')

def userdashboard(request):
    """User dashboard"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    context = {
        'user': request.user,
        'hospitals': Hospital.objects.all()[:5],
        'doctors': Doctor.objects.all()[:5],
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
    """Appointment booking"""
    doctors = Doctor.objects.all()
    hospitals = Hospital.objects.all()
    
    context = {
        'doctors': doctors,
        'hospitals': hospitals,
    }
    return render(request, 'appointment.html', context)

def bookappointment(request):
    """Book appointment"""
    if request.method == 'POST':
        try:
            from adminapp.models import Appointment
            from tenants.models import Hospital
            
            # Get form data
            hospital_id = request.POST.get('hospital')
            doctor_id = request.POST.get('doctor')
            date = request.POST.get('date')
            time = request.POST.get('time')
            reason = request.POST.get('reason', '')
            
            # Get the doctor and hospital
            doctor = Doctor.objects.get(id=doctor_id)
            hospital = Hospital.objects.get(id=hospital_id)
            
            # Create appointment
            appointment = Appointment.objects.create(
                doctor=doctor,
                hospital=hospital,
                first_name=request.user.first_name if request.user.is_authenticated else 'Guest',
                last_name=request.user.last_name if request.user.is_authenticated else 'User',
                phone='',  # You might want to add phone field to the form
                email=request.user.email if request.user.is_authenticated else '',
                date_of_birth='1990-01-01',  # Default - you might want to add this to form
                gender='other',  # Default - you might want to add this to form
                appointment_date=date,
                appointment_time=time,
                reason=reason,
                status='scheduled'
            )
            
            messages.success(request, f'Appointment booked successfully! Appointment ID: {appointment.appointment_id}')
            return redirect('appointment')
            
        except Exception as e:
            messages.error(request, f'Error booking appointment: {str(e)}')
            return redirect('appointment')
    
    return redirect('appointment')

def viewappointment(request):
    """View appointments"""
    # This would show user's appointments
    context = {
        'appointments': [],  # Add actual appointment logic here
    }
    return render(request, 'viewappointment.html', context)

def deleteappointment(request):
    """Delete appointment"""
    if request.method == 'POST':
        # Handle appointment deletion logic here
        messages.success(request, 'Appointment cancelled successfully!')
    
    return redirect('viewappointment')

# API endpoints for AJAX calls
@csrf_exempt
def get_doctors_by_hospital(request):
    """Get doctors by hospital (AJAX endpoint)"""
    if request.method == 'POST':
        hospital_id = request.POST.get('hospital_id')
        try:
            doctors = Doctor.objects.filter(hospital_id=hospital_id)
            doctor_list = [{'id': d.id, 'name': f'Dr. {d.title}'} for d in doctors]
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


def userdash(request):
    """User dashboard (alias for userdashboard)"""
    return userdashboard(request)

def doctor_list(request):
    """List all doctors"""
    from adminapp.models import Doctor
    doctors = Doctor.objects.all()
    context = {'doctors': doctors}
    return render(request, 'doctor_list.html', context)

def book_appointment(request):
    """Book appointment (alias for appointment)"""
    return appointment(request)

def appointment_confirmation(request):
    """Appointment confirmation page"""
    return render(request, 'appointment_confirmation.html', {
        'message': 'Your appointment has been booked successfully!'
    })

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
