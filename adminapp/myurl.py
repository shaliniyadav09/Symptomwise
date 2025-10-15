from django.urls import path 
from . import views

urlpatterns = [
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('admindash/',views.admindash, name='admindash'),
    path('addcat/',views.addcat, name='addcat'),
    path('viewcat/',views.viewcat, name='viewcat'),
    path('delviewcat/<id>',views.delviewcat, name='delviewcat'),
    path('adddoctor/',views.adddoctor, name='adddoctor'),
    path('viewdoctor/',views.viewdoctor, name='viewdoctor'),
    path('deldoctor/<id>',views.deldoctor, name='deldoctor'),
    path('editdoctor/<id>',views.editdoctor, name='editdoctor'),
    path('adminlogout/',views.adminlogout, name='adminlogout'),
    
    # AJAX endpoints for better UX
    path('ajax/delete-doctor/', views.delete_doctor_ajax, name='delete_doctor_ajax'),
    path('ajax/toggle-doctor-schedule/', views.toggle_doctor_schedule, name='toggle_doctor_schedule'),
]