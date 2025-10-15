from django.urls import path
from . import views

app_name = 'hospitals'

urlpatterns = [
    path('', views.hospital_list, name='list'),
    path('register/', views.hospital_register, name='register'),
    path('dashboard/', views.hospital_dashboard, name='dashboard'),
    path('<int:hospital_id>/', views.hospital_detail, name='detail'),
]
