from django.urls import path
from . import views
from . import whatsapp_views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chatbot_page, name='chat'),
    path('stream/', views.chat_stream, name='stream'),
    path('location/', views.get_user_location, name='location'),
    path('hospitals/', views.get_all_hospitals, name='hospitals'),
    path('whatsapp/', whatsapp_views.whatsapp_webhook, name='whatsapp_webhook'),
]