"""
Email utilities for SymptomWise appointment system
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_appointment_confirmation_email(appointment_data):
    """
    Send appointment confirmation email to patient
    
    Args:
        appointment_data (dict): Dictionary containing appointment details
    """
    try:
        # Extract appointment details
        patient_email = appointment_data.get('email')
        patient_name = f"{appointment_data.get('first_name')} {appointment_data.get('last_name')}"
        appointment_id = appointment_data.get('appointment_id')
        doctor_name = appointment_data.get('doctor_name')
        hospital_name = appointment_data.get('hospital_name')
        appointment_date = appointment_data.get('appointment_date')
        appointment_time = appointment_data.get('appointment_time')
        consultation_fee = appointment_data.get('consultation_fee', '500')
        
        # Email subject
        subject = f'Appointment Confirmation - {appointment_id} | SymptomWise'
        
        # Email context
        context = {
            'patient_name': patient_name,
            'appointment_id': appointment_id,
            'doctor_name': doctor_name,
            'hospital_name': hospital_name,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'consultation_fee': consultation_fee,
            'contact_email': 'symptomwiseprivatelimited@gmail.com',
            'contact_phone': '+91 7007292406',
            'emergency_number': '108'
        }
        
        # Render HTML email template
        html_message = render_to_string('emails/appointment_confirmation.html', context)
        plain_message = strip_tags(html_message)
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[patient_email]
        )
        email.attach_alternative(html_message, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"Appointment confirmation email sent to {patient_email} for appointment {appointment_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send appointment confirmation email: {str(e)}")
        return False

def send_appointment_reminder_email(appointment_data):
    """
    Send appointment reminder email to patient (for future use)
    
    Args:
        appointment_data (dict): Dictionary containing appointment details
    """
    try:
        # Similar structure to confirmation email but for reminders
        patient_email = appointment_data.get('email')
        patient_name = f"{appointment_data.get('first_name')} {appointment_data.get('last_name')}"
        appointment_id = appointment_data.get('appointment_id')
        
        subject = f'Appointment Reminder - {appointment_id} | SymptomWise'
        
        context = {
            'patient_name': patient_name,
            'appointment_id': appointment_id,
            'doctor_name': appointment_data.get('doctor_name'),
            'hospital_name': appointment_data.get('hospital_name'),
            'appointment_date': appointment_data.get('appointment_date'),
            'appointment_time': appointment_data.get('appointment_time'),
            'contact_email': 'symptomwiseprivatelimited@gmail.com',
            'contact_phone': '+91 7007292406'
        }
        
        html_message = render_to_string('emails/appointment_reminder.html', context)
        plain_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[patient_email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Appointment reminder email sent to {patient_email} for appointment {appointment_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send appointment reminder email: {str(e)}")
        return False

def send_appointment_cancellation_email(appointment_data):
    """
    Send appointment cancellation email to patient (for future use)
    
    Args:
        appointment_data (dict): Dictionary containing appointment details
    """
    try:
        patient_email = appointment_data.get('email')
        patient_name = f"{appointment_data.get('first_name')} {appointment_data.get('last_name')}"
        appointment_id = appointment_data.get('appointment_id')
        
        subject = f'Appointment Cancelled - {appointment_id} | SymptomWise'
        
        context = {
            'patient_name': patient_name,
            'appointment_id': appointment_id,
            'doctor_name': appointment_data.get('doctor_name'),
            'hospital_name': appointment_data.get('hospital_name'),
            'appointment_date': appointment_data.get('appointment_date'),
            'appointment_time': appointment_data.get('appointment_time'),
            'cancellation_reason': appointment_data.get('cancellation_reason', 'As requested'),
            'contact_email': 'symptomwiseprivatelimited@gmail.com',
            'contact_phone': '+91 7007292406'
        }
        
        html_message = render_to_string('emails/appointment_cancellation.html', context)
        plain_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[patient_email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        logger.info(f"Appointment cancellation email sent to {patient_email} for appointment {appointment_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send appointment cancellation email: {str(e)}")
        return False