from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
import json

from .models import Hospital, HospitalUser
from .forms import HospitalOnboardingForm, HospitalConfigForm


def select_hospital(request):
    """
    Hospital selection page for users with access to multiple hospitals
    """
    if request.user.is_authenticated:
        # Get hospitals user has access to
        user_hospitals = Hospital.objects.filter(
            hospital_users__user=request.user,
            is_active=True
        ).distinct()
    else:
        user_hospitals = Hospital.objects.none()
    
    # Get all active hospitals for demo/development
    all_hospitals = Hospital.objects.filter(is_active=True)
    
    if request.method == 'POST':
        hospital_id = request.POST.get('hospital_id')
        try:
            hospital = Hospital.objects.get(id=hospital_id, is_active=True)
            request.session['hospital_slug'] = hospital.slug
            messages.success(request, f'Switched to {hospital.name}')
            return redirect('index')
        except Hospital.DoesNotExist:
            messages.error(request, 'Invalid hospital selected')
    
    context = {
        'user_hospitals': user_hospitals,
        'all_hospitals': all_hospitals,
    }
    return render(request, 'tenants/select_hospital.html', context)


def hospital_onboarding(request):
    """
    Hospital registration and onboarding flow
    """
    if request.method == 'POST':
        form = HospitalOnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            hospital = form.save(commit=False)
            
            # Create user if not authenticated
            if not request.user.is_authenticated:
                username = form.cleaned_data['admin_email']
                email = form.cleaned_data['admin_email']
                password = form.cleaned_data['admin_password']
                
                # Check if user exists
                if User.objects.filter(username=username).exists():
                    messages.error(request, 'User with this email already exists')
                    return render(request, 'tenants/hospital_onboarding.html', {'form': form})
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=form.cleaned_data['admin_first_name'],
                    last_name=form.cleaned_data['admin_last_name']
                )
                login(request, user)
            else:
                user = request.user
            
            # Set hospital owner
            hospital.owner = user
            
            # Generate slug from name
            hospital.slug = slugify(hospital.name)
            
            # Set trial period (30 days)
            hospital.trial_ends_at = timezone.now() + timedelta(days=30)
            
            hospital.save()
            
            # Create hospital user relationship
            HospitalUser.objects.create(
                hospital=hospital,
                user=user,
                role='owner'
            )
            
            # Set session
            request.session['hospital_slug'] = hospital.slug
            
            messages.success(request, f'Welcome to {hospital.name}! Your hospital has been created successfully.')
            return redirect('hospital_setup', hospital_id=hospital.id)
    else:
        form = HospitalOnboardingForm()
    
    return render(request, 'tenants/hospital_onboarding.html', {'form': form})


@login_required
def hospital_setup(request, hospital_id):
    """
    Hospital configuration and setup wizard
    """
    hospital = get_object_or_404(Hospital, id=hospital_id, owner=request.user)
    
    if request.method == 'POST':
        form = HospitalConfigForm(request.POST, request.FILES, instance=hospital)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hospital configuration updated successfully!')
            return redirect('admindash')
    else:
        form = HospitalConfigForm(instance=hospital)
    
    context = {
        'hospital': hospital,
        'form': form,
    }
    return render(request, 'tenants/hospital_setup.html', context)


@login_required
def hospital_dashboard(request):
    """
    Hospital management dashboard for owners/admins
    """
    # Get hospitals user owns or manages
    hospitals = Hospital.objects.filter(
        hospital_users__user=request.user,
        hospital_users__role__in=['owner', 'admin']
    ).distinct()
    
    context = {
        'hospitals': hospitals,
    }
    return render(request, 'tenants/hospital_dashboard.html', context)


@login_required
def hospital_settings(request, hospital_id):
    """
    Hospital settings and configuration
    """
    hospital = get_object_or_404(Hospital, id=hospital_id)
    
    # Check permissions
    if not HospitalUser.objects.filter(
        hospital=hospital,
        user=request.user,
        role__in=['owner', 'admin']
    ).exists():
        messages.error(request, 'You do not have permission to access this hospital settings')
        return redirect('hospital_dashboard')
    
    if request.method == 'POST':
        form = HospitalConfigForm(request.POST, request.FILES, instance=hospital)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
    else:
        form = HospitalConfigForm(instance=hospital)
    
    context = {
        'hospital': hospital,
        'form': form,
    }
    return render(request, 'tenants/hospital_settings.html', context)


@login_required
def hospital_users(request, hospital_id):
    """
    Manage hospital users and roles
    """
    hospital = get_object_or_404(Hospital, id=hospital_id)
    
    # Check permissions
    if not HospitalUser.objects.filter(
        hospital=hospital,
        user=request.user,
        role__in=['owner', 'admin']
    ).exists():
        messages.error(request, 'You do not have permission to manage users')
        return redirect('hospital_dashboard')
    
    hospital_users = HospitalUser.objects.filter(hospital=hospital).select_related('user')
    
    context = {
        'hospital': hospital,
        'hospital_users': hospital_users,
    }
    return render(request, 'tenants/hospital_users.html', context)


@csrf_exempt
def api_hospital_stats(request, hospital_id):
    """
    API endpoint for hospital statistics
    """
    hospital = get_object_or_404(Hospital, id=hospital_id)
    
    # Import here to avoid circular imports
    from adminapp.models import Doctor, Appointment, Category
    from myapp.models import UserInfo, Enquiry
    
    stats = {
        'doctors': Doctor.objects.filter(hospital=hospital).count(),
        'appointments': Appointment.objects.filter(hospital=hospital).count(),
        'categories': Category.objects.filter(hospital=hospital).count(),
        'patients': UserInfo.objects.filter(hospital=hospital).count(),
        'enquiries': Enquiry.objects.filter(hospital=hospital).count(),
        'subscription': hospital.subscription_plan,
        'trial_days_left': 0,
    }
    
    # Calculate trial days left
    if hospital.subscription_plan == 'trial' and hospital.trial_ends_at:
        days_left = (hospital.trial_ends_at - timezone.now()).days
        stats['trial_days_left'] = max(0, days_left)
    
    return JsonResponse(stats)