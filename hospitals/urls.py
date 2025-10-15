from django.urls import path
from . import views

app_name = 'hospitals'

urlpatterns = [
    path('', views.hospital_list, name='list'),
    path('register/', views.hospital_register, name='register'),
    path('login/', views.hospital_login, name='login'),
    path('logout/', views.hospital_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('dashboard/', views.hospital_dashboard, name='dashboard'),
    path('profile/', views.hospital_profile, name='profile'),
    path('doctors/', views.hospital_doctors, name='doctors'),
    path('doctors/add/', views.add_doctor, name='add_doctor'),
    path('doctors/edit/<int:doctor_id>/', views.edit_doctor, name='edit_doctor'),
    path('doctors/delete/<int:doctor_id>/', views.delete_doctor, name='delete_doctor'),
    path('categories/', views.categories, name='categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('doctors/<int:doctor_id>/availability/', views.manage_doctor_availability, name='manage_doctor_availability'),
    path('appointments/', views.hospital_appointments, name='appointments'),
    path('<uuid:hospital_id>/', views.hospital_detail, name='detail'),
]
