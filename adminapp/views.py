from django.shortcuts import render , redirect, get_object_or_404
from django.views.decorators.cache import cache_control
from django.contrib import messages
from .models import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
@cache_control(no_cache=True , no_store=True , must_revalidate=True)
def admindash(request): 
    if 'adminid' not in request.session:
        messages.error(request,"You are not logged in")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    
    # Add these context variables
    from myapp.models import UserInfo, Enquiry
    from .models import Doctor, Category, Appointment
    
    # Use tenant-aware counts
    if hasattr(request, 'hospital') and request.hospital:
        user_count = UserInfo.tenant_objects.count()
        book_count = Appointment.tenant_objects.count()
        cat_count = Category.tenant_objects.count()
        enq_count = Enquiry.tenant_objects.count()
    else:
        user_count = UserInfo.objects.count()
        book_count = Appointment.objects.count()
        cat_count = Category.objects.count()
        enq_count = Enquiry.objects.count()
    
    context={
        'adminid':adminid,
        'user_count': user_count,
        'book_count': book_count,
        'cat_count': cat_count,
        'enq_count': enq_count,
        'hospital': getattr(request, 'hospital', None),
    }
    return render(request,'admindash.html',context)

@cache_control(no_cache=True , no_store=True , must_revalidate=True)
def adminlogout(request):
    if 'adminid' in request.session:
        del request.session['adminid']
        messages.success(request,"you are logged out")
        return redirect('adminlogin')
    else:
        return redirect('adminlogin')

@cache_control(no_cache=True , no_store=True , must_revalidate=True)
def addcat(request): 
    if 'adminid' not in request.session:
        messages.error(request,"You are not logged in")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    context={
        'adminid':adminid,
    }
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        cat = Category(name=name,description=description)   
        cat.save()
        messages.success(request,"Category added successfully")
        return redirect('addcat') # call addcat
    return render(request,'addcat.html',context)

@cache_control(no_cache=True , no_store=True , must_revalidate=True)
def viewcat(request): 
    if 'adminid' not in request.session:
        messages.error(request, "You are not logged in")
        return redirect('adminlogin')

    adminid = request.session.get('adminid')
    # Use tenant-aware queryset
    cats = Category.tenant_objects.all() if hasattr(request, 'hospital') and request.hospital else Category.objects.all()

    context = {
        'adminid': adminid,
        'cats': cats,
        'hospital': getattr(request, 'hospital', None),
    }

    return render(request, 'viewcat.html', context) 

def delviewcat(request ,id ): 
    if 'adminid' not in request.session:
        messages.error(request,"You are not logged in")
        return redirect('adminlogin')
    
    try:
        # Use tenant-aware deletion
        if hasattr(request, 'hospital') and request.hospital:
            cat = Category.tenant_objects.get(id=id)
        else:
            cat = Category.objects.get(id=id)
        cat.delete()
        messages.success(request,"category deleted successfully")
    except Category.DoesNotExist:
        messages.error(request,"Category not found")
    except Exception as e:
        messages.error(request, f"Error deleting category: {str(e)}")
    
    return redirect('viewcat')


@cache_control(no_cache=True , no_store=True , must_revalidate=True)
def adddoctor(request): 
    if 'adminid' not in request.session:
        messages.error(request,"You are not logged in")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    # Use tenant-aware queryset
    cats = Category.tenant_objects.all() if hasattr(request, 'hospital') and request.hospital else Category.objects.all()
    context={
        'adminid':adminid,
        'cats':cats
    }
    if request.method =="POST":
        try:
            title=request.POST.get('title', 'Dr.')
            first_name=request.POST.get('first_name', '').strip()
            last_name=request.POST.get('last_name', '').strip()
            category=request.POST.get('category')
            experience_years=request.POST.get('experience', 5)   # Default to 5 years
            education=request.POST.get('education', '')
            bio=request.POST.get('description', '')                  
            languages=request.POST.get('language', 'English')   
            profile_image=request.FILES.get('cover_image')      
            consultation_start_time=request.POST.get('consultation_start')
            consultation_end_time=request.POST.get('consultation_end')
            consultation_days=request.POST.get('consultation_days')
            
            # Validate required fields
            if not first_name or not last_name or not category:
                messages.error(request, "First name, last name, and category are required.")
                return render(request,'adddoctor.html',context)
            
            # Get category object
            try:
                cat = Category.objects.get(id=category)
            except Category.DoesNotExist:
                messages.error(request, "Invalid category selected.")
                return render(request,'adddoctor.html',context)
            
            # Convert experience to integer with proper validation
            try:
                experience_years = int(experience_years) if experience_years else 5
                if experience_years < 0:
                    experience_years = 5
            except (ValueError, TypeError):
                experience_years = 5
            
            # Create doctor with all required fields
            b = Doctor(
                title=title,
                first_name=first_name,
                last_name=last_name,
                experience_years=experience_years,
                category=cat,
                bio=bio,
                education=education,
                languages=languages,
                consultation_start_time=consultation_start_time,
                consultation_end_time=consultation_end_time,
                consultation_days=[consultation_days] if consultation_days else [],
                profile_image=profile_image,
                consultation_fee=500.00,  # Default consultation fee
                is_available=True,  # Default to available
            )
            b.save()
            
            messages.success(request, f"Dr. {first_name} {last_name} added successfully!")
            return redirect('viewdoctor')
            
        except Exception as e:
            messages.error(request, f"Error adding doctor: {str(e)}")
            return render(request,'adddoctor.html',context)
    return render(request,'adddoctor.html',context)

@cache_control(no_cache=True , no_store=True , must_revalidate=True)
def viewdoctor(request): 
    if 'adminid' not in request.session:
        messages.error(request,"You are not logged in")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    # Use tenant-aware queryset
    doctor = Doctor.tenant_objects.all() if hasattr(request, 'hospital') and request.hospital else Doctor.objects.all()
    context={
        'adminid':adminid,
         'doctor':doctor,
         'hospital': getattr(request, 'hospital', None),
    }
    return render(request,'viewdoctor.html',context)

def deldoctor(request, id): 
    """Delete doctor with proper error handling and tenant awareness"""
    if 'adminid' not in request.session:
        messages.error(request,"You are not logged in")
        return redirect('adminlogin')
    
    try:
        # Use tenant-aware deletion
        if hasattr(request, 'hospital') and request.hospital:
            doctor = Doctor.tenant_objects.get(id=id)
        else:
            doctor = Doctor.objects.get(id=id)
        
        doctor_name = f"{doctor.title} {doctor.first_name} {doctor.last_name}"
        doctor.delete()
        messages.success(request, f"{doctor_name} deleted successfully")
        
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor not found")
    except Exception as e:
        messages.error(request, f"Error deleting doctor: {str(e)}")
    
    return redirect('viewdoctor')

@csrf_exempt
def delete_doctor_ajax(request):
    """AJAX endpoint for deleting doctors"""
    if request.method == 'POST':
        if 'adminid' not in request.session:
            return JsonResponse({'success': False, 'message': 'Not authenticated'})
        
        try:
            doctor_id = request.POST.get('doctor_id')
            if not doctor_id:
                return JsonResponse({'success': False, 'message': 'Doctor ID required'})
            
            # Use tenant-aware deletion
            if hasattr(request, 'hospital') and request.hospital:
                doctor = Doctor.tenant_objects.get(id=doctor_id)
            else:
                doctor = Doctor.objects.get(id=doctor_id)
            
            doctor_name = f"{doctor.title} {doctor.first_name} {doctor.last_name}"
            doctor.delete()
            
            return JsonResponse({
                'success': True, 
                'message': f'{doctor_name} deleted successfully'
            })
            
        except Doctor.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Doctor not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@cache_control(no_cache=True , no_store=True , must_revalidate=True)
def editdoctor(request ,id): #update
    if 'adminid' not in request.session:
        messages.error(request,"You are not logged in")
        return redirect('adminlogin')
    adminid=request.session.get('adminid')
    
    try:
        # Use tenant-aware querysets
        if hasattr(request, 'hospital') and request.hospital:
            doctor = Doctor.tenant_objects.get(id=id)
            cats = Category.tenant_objects.all()
        else:
            doctor = Doctor.objects.get(id=id)
            cats = Category.objects.all()
    except Doctor.DoesNotExist:
        messages.error(request, "Doctor not found")
        return redirect('viewdoctor')

    context={
        'adminid':adminid,
        'doctor':doctor,
        'cats':cats
    }
    
    if request.method =="POST":
        try:
            title=request.POST.get('title')
            first_name=request.POST.get('first_name', doctor.first_name)
            last_name=request.POST.get('last_name', doctor.last_name)
            category=request.POST.get('category')
            cats = Category.objects.get(id=category)
            experience_years=request.POST.get('experience', doctor.experience_years)
            education=request.POST.get('education')
            languages=request.POST.get('language', doctor.languages)
            consultation_start_time=request.POST.get('consultation_start')
            consultation_end_time=request.POST.get('consultation_end')
            consultation_days=request.POST.get('consultation_days')
            bio=request.POST.get('description')
            profile_image=request.FILES.get('cover_image')
            
            # Convert experience to integer
            try:
                experience_years = int(experience_years) if experience_years else 0
            except ValueError:
                experience_years = doctor.experience_years

            doctor.title=title
            doctor.first_name=first_name
            doctor.last_name=last_name
            doctor.experience_years=experience_years
            doctor.category=cats
            doctor.bio=bio
            doctor.education=education
            doctor.consultation_start_time=consultation_start_time
            doctor.consultation_end_time=consultation_end_time
            doctor.consultation_days=[consultation_days] if consultation_days else []
            doctor.languages=languages
            if profile_image:
                  doctor.profile_image=profile_image
       
            doctor.save()
            messages.success(request,f"{title} {first_name} {last_name} updated successfully")
            return redirect('viewdoctor')
            
        except Exception as e:
            messages.error(request, f"Error updating doctor: {str(e)}")
            return render(request,'editdoctor.html',context)

    return render(request,'editdoctor.html',context)

@csrf_exempt
def toggle_doctor_schedule(request):
    """AJAX endpoint for toggling doctor availability/schedule"""
    if request.method == 'POST':
        if 'adminid' not in request.session:
            return JsonResponse({'success': False, 'message': 'Not authenticated'})
        
        try:
            doctor_id = request.POST.get('doctor_id')
            if not doctor_id:
                return JsonResponse({'success': False, 'message': 'Doctor ID required'})
            
            # Use tenant-aware query
            if hasattr(request, 'hospital') and request.hospital:
                doctor = Doctor.tenant_objects.get(id=doctor_id)
            else:
                doctor = Doctor.objects.get(id=doctor_id)
            
            # Toggle availability
            doctor.is_available = not doctor.is_available
            doctor.save()
            
            status = "available" if doctor.is_available else "unavailable"
            doctor_name = f"{doctor.title} {doctor.first_name} {doctor.last_name}"
            
            return JsonResponse({
                'success': True, 
                'message': f'{doctor_name} is now {status}',
                'is_available': doctor.is_available
            })
            
        except Doctor.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Doctor not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def doctor_list(request):
    """List all doctors"""
    from .models import Doctor
    from django.shortcuts import render
    
    doctors = Doctor.objects.all()
    context = {'doctors': doctors}
    return render(request, 'adminapp/doctor_list.html', context)