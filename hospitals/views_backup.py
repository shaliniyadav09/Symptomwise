from django.shortcuts import render
from django.http import JsonResponse
from tenants.models import Hospital

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
        # Handle hospital registration logic here
        return render(request, 'hospitals/register_success.html')
    
    return render(request, 'hospitals/register.html')

def hospital_dashboard(request):
    """Hospital dashboard"""
    return render(request, 'hospitals/dashboard.html')

def hospital_detail(request, hospital_id):
    """Hospital detail view"""
    try:
        hospital = Hospital.objects.get(id=hospital_id)
        context = {'hospital': hospital}
        return render(request, 'hospitals/detail.html', context)
    except Hospital.DoesNotExist:
        context = {'error': 'Hospital not found'}
        return render(request, 'hospitals/detail.html', context)
