
from django.urls import path
from myapp import views



urlpatterns = [
    path('appointment/', views.appointment, name='appointment'),
    path('bookappointment/', views.bookappointment, name='bookappointment'),

    path('',views.index ,name="index"),
    path('about/', views.about, name="about"),
    path('services/', views.services, name="services"),
    path('adminlogin/', views.adminlogin, name="adminlogin"),
    path('adminlog/', views.adminlog, name="adminlog"),
    path('contact/', views.contact, name="contact"),
    path('register/', views.register, name="register"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="logout"),
    path('userdash/', views.userdash, name="userdash"),
    path('userdashboard/', views.userdashboard, name="userdashboard"),
    path('userprofile/', views.userprofile, name="userprofile"),
    path('doctor_list/<int:id>/', views.doctor_list, name="doctor_list"),
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    path('appointment/confirmation/<str:appointment_id>/', views.appointment_confirmation, name='appointment_confirmation'),
    path('appointments/', views.viewappointment, name='view_appointments'),
    path('appointments/cancel/<str:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/cancel-page/<str:appointment_id>/', views.cancel_appointment_page, name='cancel_appointment_page'),
    path("get-available-slots/", views.get_available_slots, name="get_available_slots"),
    path('get-doctors-by-hospital/', views.get_doctors_by_hospital, name='get_doctors_by_hospital'),
    path('get-hospital-info/', views.get_hospital_info, name='get_hospital_info'),
    path('system-status/', views.system_status, name='system_status'),
    path('doctors/', views.all_doctors, name='all_doctors'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
]

    # path('login/', views.login, name="login"),
