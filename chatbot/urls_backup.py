from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    # Main chat interface
    path('', views.chat_interface, name='chat'),
    
    # Chat API endpoints
    path('send/', views.send_message, name='send_message'),
    path('session/update/', views.update_session_info, name='update_session'),
    
    # Triage system endpoints
    path('followup/', views.submit_follow_up_answers, name='submit_followup'),
    path('emergency/', views.get_emergency_resources, name='emergency_resources'),
    
    # Doctor and hospital APIs
    path('api/doctors/', views.get_doctor_recommendations, name='doctor_recommendations'),
    path('api/hospitals/', views.get_hospitals, name='hospitals'),
    
    # WhatsApp integration
    path('whatsapp/webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),
    path('test-whatsapp/', views.test_whatsapp, name='test_whatsapp'),
]
