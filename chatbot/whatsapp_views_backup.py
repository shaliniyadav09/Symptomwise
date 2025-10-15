from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import json
import requests
import logging

# IMPORTANT: Ensure your imports correctly reflect your project structure
# Assuming adminapp.models has Doctor and Category, and tenants.models has Hospital
try:
    from adminapp.models import Doctor, Category
    from tenants.models import Hospital
except ImportError:
    # Fallback or placeholder for demonstration if models aren't available
    class Doctor: 
        objects = type('MockManager', (object,), {'filter': lambda *args, **kwargs: [], 'select_related': lambda *args, **kwargs: type('MockQuerySet', (object,), {'order_by': lambda *args, **kwargs: []})})()
        full_name = "Mock Doctor"
        bio = "General Practitioner"
        experience = "10 Years"
        hospital = type('MockHospital', (object,), {'name': 'Mock Hospital', 'phone': '999-000-1111'})
    class Category: 
        objects = type('MockManager', (object,), {'get': lambda *args, **kwargs: type('MockCategory', (object,), {'name': 'General Practitioner'})})()
        name = "General Practitioner"
    class Hospital: 
        objects = type('MockManager', (object,), {'filter': lambda *args, **kwargs: []})()
        name = "Mock Hospital"
        address = "123 Main St"
        city = "Gorakhpur"
        state = "UP"
        phone = "999-000-1111"
    
    # Initialize logger here since it might be needed by the fallback classes
    logger = logging.getLogger(__name__)
    logger.warning("Could not import Django models. Database functions will use mocks and fail in a real environment.")

# Initialize logger (if not done in the ImportError block)
if 'logger' not in locals():
    logger = logging.getLogger(__name__)

# Initialize Twilio client
# Ensure TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are set in settings.py
try:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
except AttributeError:
    # Mock Client for local testing without settings
    class MockTwilioClient:
        def __init__(self, *args): pass
        @property
        def messages(self):
            return self
        def create(self, **kwargs):
            logger.warning("Twilio client not fully initialized (missing settings). Using mock client.")
            return type('MockMessage', (object,), {'sid': 'SM_MOCK'})()
    client = MockTwilioClient()
except Exception as e:
    logger.error(f"Failed to initialize Twilio client: {e}")
    class MockTwilioClient:
        def __init__(self, *args): pass
        @property
        def messages(self):
            return self
        def create(self, **kwargs):
            logger.warning("Twilio client not fully initialized. Using mock client.")
            return type('MockMessage', (object,), {'sid': 'SM_MOCK'})()
    client = MockTwilioClient()


# Store user sessions (in production, use Django Cache, Redis, or database)
user_sessions = {}

@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_webhook(request):
    """Handle incoming WhatsApp messages"""
    try:
        # Get message details
        from_number = request.POST.get('From', '')
        message_body = request.POST.get('Body', '').strip()
        
        # Create response
        response = MessagingResponse()
        
        # Process the message
        reply_text = process_whatsapp_message(from_number, message_body)
        
        # Send reply
        response.message(reply_text)
        
        return HttpResponse(str(response), content_type='text/xml')
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error for {request.POST.get('From')}: {str(e)}")
        # Send a user-friendly error response
        response = MessagingResponse()
        response.message("❌ Sorry, a critical error occurred. Please try again later.")
        return HttpResponse(str(response), content_type='text/xml')

# ----------------------------------------------------------------------
# State and Message Processing Functions
# ----------------------------------------------------------------------

def process_whatsapp_message(from_number, message_body):
    """Process WhatsApp message and return response"""
    try:
        # Normalize the number (remove 'whatsapp:') for clean session key
        session_key = from_number.replace('whatsapp:', '')
        
        # Get or create user session
        if session_key not in user_sessions:
            user_sessions[session_key] = {
                'state': 'welcome',
                'location': None,  # Stores city or coordinates
                'conversation_history': []
            }
        
        session = user_sessions[session_key]
        
        # Reset state if user types 'reset' or 'menu'
        if message_body.lower() in ['reset', 'menu']:
            # Preserve location if set, but reset flow states
            location_memory = session.get('location')
            user_sessions[session_key] = {
                'state': 'welcome',
                'location': location_memory,
                'conversation_history': []
            }
            session = user_sessions[session_key]
            return "Session reset. " + handle_welcome_state(session_key, 'hi', session)
        
        # Handle 'hi' separately to restart conversation properly
        if message_body.lower() in ['hi', 'hello', 'hey', 'start']:
            # Reset everything for a fresh start
            user_sessions[session_key] = {
                'state': 'welcome',
                'location': None,
                'conversation_history': []
            }
            session = user_sessions[session_key]
            return handle_welcome_state(session_key, message_body, session)

        session['conversation_history'].append({'user': message_body})
        
        # Handle different states
        if session['state'] == 'welcome':
            return handle_welcome_state(session_key, message_body, session)
        elif session['state'] == 'asking_location':
            return handle_location_state(session_key, message_body, session)
        elif session['state'] == 'chatting':
            return handle_chat_state(session_key, message_body, session)
        else:
            # Default to welcome state if state is invalid
            session['state'] = 'welcome'
            return handle_welcome_state(session_key, message_body, session)
            
    except Exception as e:
        logger.error(f"Error processing WhatsApp message for {session_key}: {str(e)}")
        return "Sorry, I encountered an internal error. Please try again later."

# ----------------------------------------------------------------------
# State Handlers
# ----------------------------------------------------------------------

def handle_welcome_state(from_number, message_body, session):
    """Handle welcome state with proper location flow"""
    # Check if this is a greeting
    greetings = ['hi', 'hello', 'hey', 'start', 'hola']
    if any(greeting in message_body.lower() for greeting in greetings):
        # Ask for location first
        session['state'] = 'asking_location'
        return ("*Hello! I'm SymptomWise AI, your healthcare assistant.*\n\n"
                "I'm here to help you understand your symptoms and guide you to appropriate healthcare.\n\n"
                "To provide better recommendations, please share your *city name* (e.g., Gorakhpur, Delhi, Mumbai).\n\n"
                "_Or type 'skip' to continue without location._")
    else:
        # If not a greeting, treat as symptom and set default location
        session['state'] = 'chatting'
        if not session['location']:
            session['location'] = 'Gorakhpur'  # Default location
        session['question_count'] = 0
        session['initial_symptom'] = message_body
        session['question_count'] = 1
        return "What other symptoms do you feel along with this?"

def handle_location_state(from_number, message_body, session):
    """Handle location input state"""
    if message_body.lower() == 'skip':
        session['location'] = 'Gorakhpur'  # Default location
    else:
        # Save the city name as location
        session['location'] = message_body.strip().title()
    
    # Move to chatting state
    session['state'] = 'chatting'
    session['question_count'] = 0
    
    return (f"*Great! Location set to: {session['location']}*\n\n"
            "Now, please describe your *symptoms or health concerns*.\n\n"
            "_Be as detailed as possible to help me provide better guidance._")

def handle_chat_state(from_number, message_body, session):
    """Handle medical chat with maximum 1 follow-up question"""
    try:
        # Check for emergency keywords
        emergency_keywords = [
            'bleeding', 'blood', 'chest pain', 'heart attack', 'stroke', 'unconscious',
            'difficulty breathing', 'severe pain', 'accident', 'injury', 'broken bone',
            'head injury', 'poisoning', 'overdose', 'suicide', 'emergency', 'urgent'
        ]
        
        is_emergency = any(keyword in message_body.lower() for keyword in emergency_keywords)
        
        if is_emergency:
            return handle_emergency(session)
        
        # Track question count
        if 'question_count' not in session:
            session['question_count'] = 0
        
        # ----------------------------------------------------------
        # 1. First symptom description -> Ask follow-up question
        # ----------------------------------------------------------
        if session['question_count'] == 0:
            session['question_count'] = 1
            session['initial_symptom'] = message_body
            return "What other symptoms do you feel along with this?"
        
        # ----------------------------------------------------------
        # 2. Second message (follow-up response) -> Provide diagnosis
        # ----------------------------------------------------------
        elif session['question_count'] == 1:
            session['question_count'] = 2
            session['follow_up_symptoms'] = message_body
            
            # Combine initial symptom with additional symptoms
            combined_symptoms = f"{session.get('initial_symptom', '')} {message_body}"
            
            # Get AI response for combined symptoms
            ai_response = get_ai_response(combined_symptoms, session)
            
            # Check urgency level
            triage = extract_triage_level_whatsapp(combined_symptoms + " " + ai_response)
            
            if triage in ['URGENT', 'SEMI-URGENT']:
                # For urgent/semi-urgent cases, show doctors immediately
                response_text = ai_response + "\n\n"
                
                if triage == 'URGENT':
                    response_text += "*🚨 URGENT: Your symptoms require immediate medical attention!*\n\n"
                else:
                    response_text += "*⚠️ SEMI-URGENT: Please see a healthcare professional within 24-48 hours.*\n\n"
                
                # Show doctors and hospitals immediately
                recommendations = process_medical_response_whatsapp(ai_response, session['location'], combined_symptoms)
                if recommendations:
                    response_text += format_recommendations_whatsapp(recommendations)
                else:
                    response_text += "Please visit: https://symptomwise.loca.lt/appointment/"
                
                session['conversation_history'].append({'ai': response_text})
                # Set a flag to stop the appointment decision flow
                session['awaiting_appointment_decision'] = False
                return response_text
            else:
                # For routine cases, show remedies first
                remedies = extract_remedies_whatsapp(combined_symptoms)
                response_text = ai_response + "\n\n"
                
                if remedies:
                    response_text += "*🏠 Home Remedies & Self-Care:*\n"
                    for remedy in remedies:
                        response_text += f"• {remedy}\n"
                    response_text += "\n"
                
                response_text += "*💊 Need Professional Care?*\n"
                response_text += "If symptoms persist or worsen, reply with '*book appointment*' to see nearby doctors and hospitals.\n\n"
                response_text += "Or reply '*feeling better*' if the remedies help."
                
                session['conversation_history'].append({'ai': response_text})
                # Set flag to await user decision for appointment
                session['awaiting_appointment_decision'] = True
                
                return response_text
        
        # ----------------------------------------------------------
        # 3. Handle appointment booking requests after diagnosis (Step 2)
        # ----------------------------------------------------------
        elif session.get('awaiting_appointment_decision'):
            if 'book appointment' in message_body.lower() or 'appointment' in message_body.lower():
                # Show doctors and hospitals
                combined_symptoms = f"{session.get('initial_symptom', '')} {session.get('follow_up_symptoms', '')}"
                recommendations = process_medical_response_whatsapp("", session['location'], combined_symptoms)
                
                response_text = "*👩‍⚕️ Here are your healthcare options:*\n\n"
                
                if recommendations:
                    response_text += format_recommendations_whatsapp(recommendations)
                else:
                    response_text += "Please visit our website to find doctors and book appointments:\n"
                    response_text += "https://symptomwise.loca.lt/appointment/"
                
                session['awaiting_appointment_decision'] = False
                return response_text
            
            elif 'feeling better' in message_body.lower() or 'better' in message_body.lower():
                session['awaiting_appointment_decision'] = False
                return "*😊 Great to hear you're feeling better!*\n\nRemember to:\n• Continue following the remedies\n• Stay hydrated\n• Get adequate rest\n\nIf symptoms return or worsen, don't hesitate to seek medical care. Type 'hi' for a new consultation."
            
            else:
                # If the user responds with something else while awaiting a decision
                return "Please reply with '*book appointment*' if you need medical care, or '*feeling better*' if the remedies are helping."
        
        # ----------------------------------------------------------
        # 4. Handle any other messages after the main flow is complete (The Fix)
        # ----------------------------------------------------------
        else:
            # The flow is already complete (question_count >= 2 and not awaiting decision).
            # We re-check for the appointment command one last time.
            if 'book appointment' in message_body.lower() or 'appointment' in message_body.lower():
                combined_symptoms = f"{session.get('initial_symptom', '')} {session.get('follow_up_symptoms', '')}"
                recommendations = process_medical_response_whatsapp("", session['location'], combined_symptoms)
                
                response_text = "*👩‍⚕️ Here are your healthcare options:*\n\n"
                
                if recommendations:
                    response_text += format_recommendations_whatsapp(recommendations)
                else:
                    response_text += "We couldn't find specific recommendations. Please visit our website to find doctors and book appointments:\n"
                    response_text += "https://symptomwise.loca.lt/appointment/"
                
                return response_text
            
            # Final message if the user keeps chatting after the consultation
            return "Thank you for the information. Please consult with the recommended doctors or visit the suggested hospitals for proper medical care. Type 'hi' to start a new consultation."
            
    except Exception as e:
        logger.error(f"Error in chat state: {str(e)}")
        return "I'm having trouble processing your request. Please try again."

# ----------------------------------------------------------------------
# AI and Database Utility Functions (Unchanged for the fix)
# ----------------------------------------------------------------------

def handle_emergency(session):
    """Handle emergency situations"""
    emergency_text = ("*🚨 EMERGENCY DETECTED 🚨*\n\n"
                      "🛑 *Call 108 (India) or your local emergency number IMMEDIATELY!* 🛑\n"
                      "Do not wait for a chat response.\n\n"
                      "---")
    
    # Get emergency hospitals
    hospitals = get_emergency_hospitals_whatsapp(session['location'])
    
    if hospitals:
        emergency_text += "\n*Nearby Hospitals (Contact ASAP):*\n"
        for hospital in hospitals[:3]:
            emergency_text += f"\n*🏥 {hospital['name']}*\n"
            emergency_text += f"📞 Phone: {hospital['phone']}\n"
            emergency_text += f"📍 Address: {hospital['address']}, {hospital['city']}"
    else:
        emergency_text += "\n*Please seek the nearest hospital immediately.*"
    
    return emergency_text

def get_ai_response(message, session):
    """Get response from AI model (Ollama)"""
    try:
        # Add a simple system prompt or conversation history to improve context
        history_prompt = "You are SymptomWise AI, a helpful, cautious, and non-diagnostic medical assistant. Keep responses brief and focused. Based on the user's input, suggest a medical specialty for a doctor consultation, if applicable. User location: " + str(session['location']) + ". User message: "

        payload = {
            "model": "symptomwise", # Ensure this model name is correct on your Ollama server
            "prompt": history_prompt + message,
            "stream": False
        }
        
        # Ensure Ollama server is running at http://localhost:11434
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'I apologize, but I cannot process your request right now.')
        else:
            logger.error(f"Ollama API error: Status {response.status_code}, Response: {response.text}")
            return "I'm having trouble connecting to my medical knowledge base. Please try again."
            
    except requests.exceptions.ConnectionError:
        logger.error("Ollama connection error: Is http://localhost:11434/api/generate running?")
        return "I'm experiencing technical difficulties. My AI core is offline. Please try again later."
    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        return "I'm experiencing technical difficulties. Please try again later."

def process_medical_response_whatsapp(response_text, user_location, user_message):
    """Process medical response to find local recommendations."""
    try:
        recommendations = {
            'specialty': None,
            'doctors': [],
            'hospitals': []
        }
        
        # 1. Extract specialty
        specialty = extract_specialty_whatsapp(response_text)
        recommendations['specialty'] = specialty
        
        # 2. Find Doctors
        if specialty:
            doctors = find_doctors_by_specialty_whatsapp(specialty, user_location)
            recommendations['doctors'] = doctors
        
        # 3. Find Hospitals (simple location filtering)
        hospitals = find_nearby_hospitals_whatsapp(user_location)
        recommendations['hospitals'] = hospitals
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error processing medical response: {str(e)}")
        return None

def extract_remedies_whatsapp(user_message):
    """Extract home remedies for WhatsApp based on symptoms"""
    remedies = []
    
    # Common remedy patterns
    remedy_keywords = {
        'headache': [
            'Stay hydrated - drink plenty of water',
            'Get adequate rest in a dark, quiet room',
            'Apply cold compress to forehead',
            'Try herbal teas like peppermint or ginger'
        ],
        'fever': [
            'Monitor temperature regularly',
            'Increase fluid intake',
            'Get plenty of rest',
            'Use lukewarm sponge baths to cool down'
        ],
        'cough': [
            'Honey and warm water can soothe throat',
            'Use a humidifier or steam inhalation',
            'Drink warm herbal teas',
            'Avoid irritants like smoke'
        ],
        'cold': [
            'Stay well hydrated',
            'Gargle with warm salt water',
            'Get extra sleep and rest',
            'Eat warm, nutritious soups'
        ],
        'stomach': [
            'Try ginger tea for nausea',
            'Eat bland foods like bananas and rice',
            'Stay hydrated with small sips',
            'Rest and avoid heavy meals'
        ]
    }
    
    # Check user message for symptoms
    user_lower = user_message.lower()
    for symptom, remedy_list in remedy_keywords.items():
        if symptom in user_lower:
            remedies.extend(remedy_list)
            break
    
    # If no specific remedies found, provide general wellness tips
    if not remedies:
        remedies = [
            'Stay well hydrated throughout the day',
            'Ensure adequate rest and sleep',
            'Maintain a balanced, nutritious diet',
            'Light exercise if feeling up to it'
        ]
    
    return remedies[:3]  # Return max 3 remedies for WhatsApp

def extract_triage_level_whatsapp(text):
    """Extract triage level for WhatsApp from symptoms and AI response"""
    text_lower = text.lower()
    
    # Urgent symptoms
    urgent_keywords = [
        'chest pain', 'difficulty breathing', 'severe pain', 'bleeding heavily',
        'unconscious', 'seizure', 'stroke', 'heart attack', 'severe headache',
        'high fever', 'vomiting blood', 'severe abdominal pain', 'broken bone',
        'head injury', 'poisoning', 'overdose', 'suicide', 'emergency', 'urgent',
        'severe', 'critical', 'immediate', "can't breathe", 'choking'
    ]
    
    # Semi-urgent symptoms
    semi_urgent_keywords = [
        'persistent fever', 'severe cough', 'persistent vomiting', 'dehydration',
        'severe diarrhea', 'moderate pain', 'infection', 'rash spreading',
        'swelling', 'difficulty swallowing', 'persistent headache', 'dizziness',
        'fainting', 'irregular heartbeat', 'shortness of breath', 'semi-urgent',
        'soon', '24-48 hours', 'within days', 'worsening'
    ]
    
    if any(keyword in text_lower for keyword in urgent_keywords):
        return 'URGENT'
    elif any(keyword in text_lower for keyword in semi_urgent_keywords):
        return 'SEMI-URGENT'
    else:
        return 'ROUTINE'

def extract_specialty_whatsapp(text):
    """Extract medical specialty from text (improved logic)"""
    text_lower = text.lower()
    
    specialties_map = {
        'cardiologist': 'Cardiologist', 'cardiology': 'Cardiologist', 'heart': 'Cardiologist',
        'neurologist': 'Neurologist', 'neurology': 'Neurologist', 'brain': 'Neurologist',
        'orthopedic': 'Orthopedic Surgeon', 'bone': 'Orthopedic Surgeon', 'joint': 'Orthopedic Surgeon',
        'dermatologist': 'Dermatologist', 'skin': 'Dermatologist', 'rash': 'Dermatologist',
        'psychiatrist': 'Psychiatrist', 'mental': 'Psychiatrist', 'depression': 'Psychiatrist',
        'ophthalmologist': 'Ophthalmologist', 'eye': 'Ophthalmologist', 'vision': 'Ophthalmologist',
        'general practitioner': 'General Practitioner', 'fever': 'General Practitioner', 'cold': 'General Practitioner',
        'dentist': 'Dentist', 'dental': 'Dentist', 'tooth': 'Dentist', 'gastroenterologist': 'Gastroenterologist', 
        'stomach': 'Gastroenterologist', 'digestive': 'Gastroenterologist'
    }
    
    for keyword, specialty in specialties_map.items():
        if keyword in text_lower:
            return specialty
    
    if any(k in text_lower for k in ['symptoms', 'general', 'checkup']):
        return 'General Practitioner'
        
    return None

def find_doctors_by_specialty_whatsapp(specialty, user_location):
    """Find doctors by specialty and optionally filter by location."""
    try:
        try:
            category_obj = Category.objects.get(name__iexact=specialty)
            
            filters = {'category': category_obj, 'is_available': True}
            
            if user_location and user_location.lower() != 'skip':
                filters['hospital__city__iexact'] = user_location

            doctors = Doctor.objects.filter(**filters).select_related('category', 'hospital').order_by('-experience')[:3]

        except Category.DoesNotExist:
            filters = {'bio__icontains': specialty, 'is_available': True}
            if user_location and user_location.lower() != 'skip':
                filters['hospital__city__iexact'] = user_location
                
            doctors = Doctor.objects.filter(**filters).select_related('category', 'hospital').order_by('-experience')[:3]
        
        doctor_list = []
        for doctor in doctors:
            doctor_data = {
                'name': doctor.full_name,
                'specialty': doctor.bio or (doctor.category.name if getattr(doctor, 'category', None) else specialty), 
                'experience': getattr(doctor, 'experience', None) or f"{getattr(doctor, 'experience_years', 'N/A')} Years",
                'hospital': getattr(doctor, 'hospital', None).name if getattr(doctor, 'hospital', None) else 'Unknown Hospital',
                'phone': getattr(doctor, 'hospital', None).phone if getattr(doctor, 'hospital', None) else 'N/A'
            }
            doctor_list.append(doctor_data)
        
        return doctor_list
        
    except Exception as e:
        logger.error(f"Error finding doctors: {str(e)}")
        return []

def find_nearby_hospitals_whatsapp(user_location):
    """Find nearby hospitals for WhatsApp, filtered by city."""
    try:
        hospitals = Hospital.objects.filter(is_active=True)
        
        if user_location and user_location.lower() != 'skip':
            hospitals = hospitals.filter(city__iexact=user_location)
        
        hospital_list = []
        for hospital in hospitals[:3]:
            hospital_data = {
                'name': hospital.name,
                'address': hospital.address,
                'city': hospital.city,
                'state': hospital.state,
                'phone': hospital.phone
            }
            hospital_list.append(hospital_data)
        
        return hospital_list
        
    except Exception as e:
        logger.error(f"Error finding hospitals: {str(e)}")
        return []

def get_emergency_hospitals_whatsapp(user_location):
    """Get emergency hospitals for WhatsApp (uses the same logic as nearby for simplicity)."""
    return find_nearby_hospitals_whatsapp(user_location)

def format_recommendations_whatsapp(recommendations):
    """Format recommendations for WhatsApp with better readability and dynamic URLs."""
    text = ""
    
    if recommendations.get('doctors'):
        text += "*🩺 Recommended Doctors (Top 2):*\n"
        for doctor in recommendations['doctors'][:2]:
            text += f"\n*Dr. {doctor['name']}* ({doctor['specialty']})\n"
            text += f"🏢 {doctor['hospital']}\n"
            text += f"⏳ Exp: {doctor['experience']}\n"
            if doctor['phone'] != 'N/A':
                text += f"📞 Call: {doctor['phone']}\n"
    
    if recommendations.get('hospitals') and not recommendations.get('doctors'):
          # Only show general nearby hospitals if no specific doctors were found
          text += "*🏥 Nearby Hospitals (Top 2):*\n"
          for hospital in recommendations['hospitals'][:2]:
              text += f"\n*{hospital['name']}*\n"
              text += f"📍 {hospital['address']}, {hospital['city']}\n"
              text += f"📞 Phone: {hospital['phone']}\n"
    
    # Dynamic appointment booking URL based on recommendations
    text += "\n---\n"
    
    if recommendations.get('doctors'):
        # If doctors found, create URL with first doctor
        appointment_url = "https://symptomwise.loca.lt/appointment/"
        text += f"*📅 Book Appointment:* {appointment_url}\n"
        text += "_Click the link above to book with recommended doctors_"
    elif recommendations.get('hospitals'):
        # If only hospitals found, create URL with first hospital
        appointment_url = "https://symptomwise.loca.lt/appointment/"
        text += f"*📅 Book Appointment:* {appointment_url}\n"
        text += "_Click the link above to book at nearby hospitals_"
    else:
        # Generic appointment booking
        appointment_url = "https://symptomwise.loca.lt/appointment/"
        text += f"*📅 Book Appointment:* {appointment_url}\n"
        text += "_Click the link above to find doctors and book appointments_"
    
    return text

# Function to send WhatsApp message (for testing outside the webhook flow)
def send_whatsapp_message(to_number, message):
    """Send WhatsApp message (Requires TWILIO_WHATSAPP_NUMBER in settings)."""
    try:
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=f'whatsapp:{to_number}'
        )
        return message.sid
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {to_number}: {str(e)}")
        return None