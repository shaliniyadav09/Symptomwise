from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import json
import requests
import logging
import time

try:
    from adminapp.models import Doctor, Category
    from tenants.models import Hospital
    from .models import ChatSession, WhatsAppSession
except ImportError:
    class Doctor: 
        objects = type('MockManager', (object,), {
            'filter': lambda *args, **kwargs: [], 
            'select_related': lambda *args, **kwargs: type('MockQuerySet', (object,), {
                'order_by': lambda *args, **kwargs: []
            })
        })()
        full_name = "Mock Doctor"
        bio = "General Practitioner"
        experience_years = 10
        hospital = type('MockHospital', (object,), {'name': 'Mock Hospital', 'phone': '999-000-1111'})
    
    class Category: 
        objects = type('MockManager', (object,), {
            'get': lambda *args, **kwargs: type('MockCategory', (object,), {'name': 'General Practitioner'})
        })()
        name = "General Practitioner"
    
    class Hospital: 
        objects = type('MockManager', (object,), {'filter': lambda *args, **kwargs: []})
        name = "Mock Hospital"
        address = "123 Main St"
        city = "Gorakhpur"
        state = "UP"
        phone = "999-000-1111"
    
    ChatSession = None
    WhatsAppSession = None
    
    logger = logging.getLogger(__name__)
    logger.warning("Could not import Django models. Database functions will use mocks and fail in a real environment.")

if 'logger' not in locals():
    logger = logging.getLogger(__name__)

try:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
except AttributeError:
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

user_sessions = {}

def get_or_create_whatsapp_session(phone_number):
    session_key = phone_number.replace('whatsapp:', '')
    
    if WhatsAppSession and ChatSession:
        try:
            whatsapp_session = WhatsAppSession.objects.filter(phone_number=session_key).first()
            if whatsapp_session:
                chat_session = whatsapp_session.chat_session
                session_data = {
                    'state': 'welcome',
                    'location': chat_session.user_preferences.get('location'),
                    'conversation_history': [],
                    'whatsapp_session_id': whatsapp_session.id,
                    'chat_session_id': chat_session.id
                }
                user_sessions[session_key] = session_data
                logger.info(f"Loaded existing WhatsApp session for {session_key} with location: {session_data.get('location')}")
                return session_data
        except Exception as e:
            logger.warning(f"Could not load WhatsApp session from database: {str(e)}")
    
    if session_key not in user_sessions:
        session_data = {
            'state': 'welcome',
            'location': None,
            'conversation_history': [],
            'whatsapp_session_id': None,
            'chat_session_id': None
        }
        
        if WhatsAppSession and ChatSession:
            try:
                chat_session = ChatSession.objects.create(
                    session_id=f'whatsapp_{session_key}_{int(time.time())}',
                    is_guest=True,
                    guest_identifier=session_key,
                    user_preferences={'location': None}
                )
                
                whatsapp_session = WhatsAppSession.objects.create(
                    phone_number=session_key,
                    chat_session=chat_session
                )
                
                session_data['whatsapp_session_id'] = whatsapp_session.id
                session_data['chat_session_id'] = chat_session.id
                
                logger.info(f"Created new WhatsApp session for {session_key}")
            except Exception as e:
                logger.warning(f"Could could not create WhatsApp session in database: {str(e)}")
        
        user_sessions[session_key] = session_data
    
    return user_sessions[session_key]

def save_location_to_session(phone_number, location):
    session_key = phone_number.replace('whatsapp:', '')
    session = user_sessions.get(session_key, {})
    
    session['location'] = location
    user_sessions[session_key] = session
    
    if WhatsAppSession and ChatSession and session.get('chat_session_id'):
        try:
            chat_session = ChatSession.objects.get(id=session['chat_session_id'])
            chat_session.user_preferences = {'location': location}
            chat_session.save()
            logger.info(f"Saved location to database for {session_key}: {location}")
        except Exception as e:
            logger.warning(f"Could not save location to database: {str(e)}")

@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_webhook(request):
    try:
        from_number = request.POST.get('From', '')
        message_body = request.POST.get('Body', '').strip()
        
        response = MessagingResponse()
        
        reply_text = process_whatsapp_message(from_number, message_body)
        
        response.message(reply_text)
        
        return HttpResponse(str(response), content_type='text/xml')
        
    except Exception as e:
        logger.error(f"WhatsApp webhook error for {request.POST.get('From')}: {str(e)}")
        response = MessagingResponse()
        response.message("❌ Sorry, a critical error occurred. Please try again later.")
        return HttpResponse(str(response), content_type='text/xml')

def process_whatsapp_message(from_number, message_body):
    try:
        session = get_or_create_whatsapp_session(from_number)
        session_key = from_number.replace('whatsapp:', '')
        
        if message_body.lower() in ['reset', 'menu']:
            location_memory = session.get('location')
            session.update({
                'state': 'welcome',
                'location': location_memory,
                'conversation_history': []
            })
            return "Session reset. " + handle_welcome_state(session_key, 'hi', session)
        
        if message_body.lower() in ['hi', 'hello', 'hey', 'start']:
            location_memory = session.get('location')
            session.update({
                'state': 'welcome' if not location_memory else 'chatting',
                'conversation_history': [],
                'question_count': 0
            })
            
            if location_memory:
                return (f"*Hello again! I'm SymptomWise AI.*\n\n"
                       f"I remember your location: *{location_memory}*\n\n"
                       f"How can I help you today? Please describe your *symptoms or health concerns*.\n\n"
                       f"_Be as detailed as possible to help me provide better guidance._")
            else:
                return handle_welcome_state(session_key, message_body, session)

        session['conversation_history'].append({'user': message_body})
        
        if session['state'] == 'welcome':
            return handle_welcome_state(session_key, message_body, session)
        elif session['state'] == 'asking_location':
            return handle_location_state(session_key, message_body, session)
        elif session['state'] == 'chatting':
            return handle_chat_state(session_key, message_body, session)
        else:
            session['state'] = 'welcome'
            return handle_welcome_state(session_key, message_body, session)
            
    except Exception as e:
        logger.error(f"Error processing WhatsApp message for {from_number}: {str(e)}")
        return "Sorry, I encountered an internal error. Please try again later."

def handle_welcome_state(from_number, message_body, session):
    greetings = ['hi', 'hello', 'hey', 'start', 'hola']
    if any(greeting in message_body.lower() for greeting in greetings):
        if session.get('location'):
            session['state'] = 'chatting'
            session['question_count'] = 0
            return (f"*Hello! I'm SymptomWise AI, your healthcare assistant.*\n\n"
                   f"I remember your location: *{session['location']}*\n\n"
                   f"How can I help you today? Please describe your *symptoms or health concerns*.\n\n"
                   f"_Be as detailed as possible to help me provide better guidance._")
        else:
            session['state'] = 'asking_location'
            return ("*Hello! I'm SymptomWise AI, your healthcare assistant.*\n\n"
                    "I'm here to help you understand your symptoms and guide you to appropriate healthcare.\n\n"
                    "To provide better recommendations, please share your *city name* (e.g., Gorakhpur, Delhi, Mumbai).\n\n"
                    "_Or type 'skip' to continue without location._")
    else:
        session['state'] = 'chatting'
        if not session.get('location'):
            session['location'] = 'Gorakhpur'
            save_location_to_session(from_number, 'Gorakhpur')
        session['question_count'] = 0
        return handle_chat_state(from_number, message_body, session)

def handle_location_state(from_number, message_body, session):
    if message_body.lower() == 'skip':
        session['location'] = 'Gorakhpur'
    else:
        session['location'] = message_body.strip().title()
    
    save_location_to_session(from_number, session['location'])
    
    session['state'] = 'chatting'
    session['question_count'] = 0
    
    return (f"*Great! Location set to: {session['location']}*\n\n"
            "Now, please describe your *symptoms or health concerns*.\n\n"
            "_Be as detailed as possible to help me provide better guidance._")

def handle_chat_state(from_number, message_body, session):
    try:
        emergency_keywords = [
            'bleeding', 'blood', 'chest pain', 'heart attack', 'stroke', 'unconscious',
            'difficulty breathing', 'severe pain', 'accident', 'injury', 'broken bone',
            'head injury', 'poisoning', 'overdose', 'suicide', 'emergency', 'urgent',
            'severe', 'critical', 'dying', 'death', 'ambulance', 'hospital now',
            'can\'t breathe', 'choking', 'seizure', 'convulsion', 'paralysis',
            'severe bleeding', 'heavy bleeding', 'vomiting blood', 'coughing blood',
            'severe headache', 'worst headache', 'sudden headache', 'blurred vision',
            'loss of consciousness', 'fainting', 'collapsed', 'not responding'
        ]
        
        is_emergency = any(keyword in message_body.lower() for keyword in emergency_keywords)
        
        if is_emergency:
            return handle_emergency(session)
        
        if 'question_count' not in session:
            session['question_count'] = 0

        # --- Check for forced diagnosis command ---
        if message_body.lower() in ['done', 'finish', 'that\'s all'] and session.get('question_count', 0) >= 1:
            session['question_count'] = 99
            # Skip to the diagnosis block below

        # --- 1. Initial Symptom Collection (Turn 1: question_count = 0 -> 1) ---
        if session.get('question_count') == 0:
            session['question_count'] = 1
            session['initial_symptom'] = message_body
            return "Thank you. To help me triage your symptoms better, please tell me: Do you have a fever, how would you rate your pain (1-10), or any specific local discomfort? (If done, just type 'done')"

        # --- 2. First Follow-up Collection (Turn 2: question_count = 1 -> 2) ---
        elif session.get('question_count') == 1:
            # FIX: Store the reply to the first follow-up question and advance to 2
            session['question_count'] = 2
            session['follow_up_symptoms_1'] = message_body
            return "Understood. Can you tell me how long you've had these symptoms, and if they are constant or intermittent? (If done, just type 'done')"

        # --- 3. Second Follow-up Collection and Diagnosis Trigger (Turn 3: question_count = 2 -> 99) ---
        elif session.get('question_count') == 2:
            # FIX: Store the reply to the second follow-up question and trigger diagnosis
            session['follow_up_symptoms_2'] = message_body 
            session['question_count'] = 99
            
        # --- 4. Diagnosis Logic (Runs if question_count is 99 or forced by 'done') ---
        if session.get('question_count') == 99:
            
            # Combine all collected symptoms
            symptoms = [session.get('initial_symptom', ''), 
                        session.get('follow_up_symptoms_1', ''), 
                        session.get('follow_up_symptoms_2', '')]
            combined_symptoms = " ".join([s for s in symptoms if s])
            
            # Get AI response with enhanced prompt
            ai_response = get_ai_response(combined_symptoms, session)
            
            # --- Triage and Response Logic ---
            triage = extract_triage_level_whatsapp(combined_symptoms + " " + ai_response)
            
            if triage == 'URGENT':
                # URGENT: Show emergency message, call 108, show hospitals
                response_text = ai_response + "\n\n"
                response_text += "*🚨 URGENT: Your symptoms require IMMEDIATE medical attention!* \n\n"
                response_text += "*📞 Call 108 for emergency services or go to the nearest emergency room NOW.* \n\n"
                
                hospitals = get_emergency_hospitals_whatsapp(session['location'])
                if hospitals:
                    response_text += "*🏥 Nearest Emergency Hospitals:* \n"
                    for hospital in hospitals[:2]:
                        response_text += f"\n*🏥 {hospital.get('name', 'Hospital')}*\n"
                        response_text += f"📞 Phone: {hospital.get('phone', 'N/A')}\n"
                        response_text += f"📍 {hospital.get('address', 'N/A')}, {hospital.get('city', 'N/A')}\n"
                else:
                    response_text += "*Please seek the nearest hospital immediately.*\n"
                
                response_text += "\n*🚨 THIS IS A MEDICAL EMERGENCY - SEEK IMMEDIATE HELP! 🚨*"
                
                session['conversation_history'].append({'ai': response_text})
                session['awaiting_appointment_decision'] = False
                return response_text
                
            elif triage == 'SEMI-URGENT':
                # SEMI-URGENT: Show warning, suggest 24-48 hours, show doctors and hospitals
                response_text = ai_response + "\n\n"
                response_text += "*⚠️ SEMI-URGENT: Please seek professional care within 24-48 hours.* \n\n"
                
                recommendations = process_medical_response_whatsapp(ai_response, session['location'], combined_symptoms)
                if recommendations:
                    response_text += format_recommendations_whatsapp(recommendations)
                else:
                    response_text += "Please visit our appointment page: https://symptomwise.loca.lt/appointment/"
                
                session['conversation_history'].append({'ai': response_text})
                session['awaiting_appointment_decision'] = False
                return response_text
                
            else:
                # ROUTINE: Show remedies only, with appointment option
                response_text = ai_response + "\n\n"
                response_text += "*ℹ️ ROUTINE: These symptoms can typically be managed with home care.* \n\n"
                
                remedies = extract_remedies_whatsapp(combined_symptoms)
                if remedies:
                    response_text += "*🏠 Home Remedies & Self-Care:* \n"
                    for remedy in remedies:
                        response_text += f"• {remedy}\n"
                    response_text += "\n"
                
                response_text += "*💊 Need Professional Care?* \n"
                response_text += "If symptoms persist or worsen, reply with '*book appointment*' or '*feeling better*'."
                
                session['conversation_history'].append({'ai': response_text})
                session['awaiting_appointment_decision'] = True
                
                return response_text
        
        # --- 5. Decision Handling (Only runs if awaiting_appointment_decision is True) ---
        elif session.get('awaiting_appointment_decision'):
            if 'book appointment' in message_body.lower() or 'appointment' in message_body.lower():
                combined_symptoms = f"{session.get('initial_symptom', '')} {session.get('follow_up_symptoms_1', '')} {session.get('follow_up_symptoms_2', '')}"
                # You may need to call get_ai_response here if the current session doesn't have it saved
                recommendations = process_medical_response_whatsapp("", session['location'], combined_symptoms)
                
                response_text = "*👩‍⚕️ Here are your healthcare options:* \n\n"
                
                if recommendations:
                    response_text += format_recommendations_whatsapp(recommendations)
                else:
                    response_text += "Please visit our website to find doctors and book appointments: \n"
                    response_text += "https://symptomwise.loca.lt/appointment/"
                
                session['awaiting_appointment_decision'] = False
                return response_text
            
            elif 'feeling better' in message_body.lower() or 'better' in message_body.lower():
                session['awaiting_appointment_decision'] = False
                return "*😊 Great to hear you're feeling better!* \n\nRemember to: \n• Continue following the remedies\n• Stay hydrated\n• Get adequate rest\n\nIf symptoms return or worsen, don't hesitate to seek medical care. Type 'hi' for a new consultation."
            
            else:
                return "Please reply with '*book appointment*' if you need medical care, or '*feeling better*' if the remedies are helping."
        
        # --- 6. Final state/fallback ---
        else:
            return "Thank you for the information. Type 'hi' to start a new consultation or 'reset' to clear our history."
            
    except Exception as e:
        logger.error(f"Error in chat state: {str(e)}")
        return "I'm having trouble processing your request. Please try again."

def handle_emergency(session):
    try:
        emergency_text = ("*🚨 EMERGENCY DETECTED 🚨*\n\n"
                          "🛑 *Call 108 (India) or your local emergency number IMMEDIATELY!* 🛑\n"
                          "Do not wait for a chat response.\n\n"
                          "---")
        
        location = session.get('location', 'Unknown') if session else 'Unknown'
        hospitals = get_emergency_hospitals_whatsapp(location)
        
        if hospitals:
            emergency_text += "\n*Nearest Emergency Hospitals:*\n"
            for hospital in hospitals[:3]:
                try:
                    emergency_text += f"\n*🏥 {hospital.get('name', 'Hospital')}*\n"
                    emergency_text += f"📞 Phone: {hospital.get('phone', 'Contact directly')}\n"
                    emergency_text += f"📍 {hospital.get('address', '')}, {hospital.get('city', '')}"
                except Exception as e:
                    logger.error(f"Error formatting hospital info: {str(e)}")
                    continue
        else:
            emergency_text += "\n*Please seek the nearest hospital immediately.*"
        
        emergency_text += "\n\n*🚨 THIS IS A MEDICAL EMERGENCY - SEEK IMMEDIATE HELP! 🚨*"
        
        return emergency_text
    except Exception as e:
        logger.error(f"Error in handle_emergency: {str(e)}")
        return "*🚨 EMERGENCY DETECTED 🚨*\n\nCall 108 immediately for emergency services! \n\nSeek immediate medical attention at the nearest hospital."

def get_ai_response(message, session):
    try:
        # Improved Prompt Engineering (sending conversation history as context)
        conversation_history = session.get('conversation_history', [])
        
        # Limit history to prevent excessive tokens
        history_summary = " ".join([entry.get('user', '') for entry in conversation_history[-3:]])

        full_prompt = (
            f"Role: SymptomWise AI (concise, non-diagnostic). Location: {session.get('location', 'Not set')}. "
            f"Prior Context: {history_summary}. "
            f"User's symptoms: {message}. "
            f"Analyze and provide ONLY: 1. Brief, cautious summary (max 3 sentences). 2. Triage (URGENT/SEMI-URGENT/ROUTINE). 3. Suggested medical specialty."
        )

        payload = {
            "model": "symptomwise",
            "prompt": full_prompt,
            "stream": False
        }
        
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
    try:
        recommendations = {
            'specialty': None,
            'doctors': [],
            'hospitals': []
        }
        
        specialty = extract_specialty_whatsapp(response_text)
        recommendations['specialty'] = specialty
        
        if specialty:
            doctors = find_doctors_by_specialty_whatsapp(specialty, user_location)
            recommendations['doctors'] = doctors
        
        hospitals = find_nearby_hospitals_whatsapp(user_location)
        recommendations['hospitals'] = hospitals
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error processing medical response: {str(e)}")
        return None

def extract_remedies_whatsapp(user_message):
    remedies = []
    
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
    
    user_lower = user_message.lower()
    for symptom, remedy_list in remedy_keywords.items():
        if symptom in user_lower:
            remedies.extend(remedy_list)
            break
    
    if not remedies:
        remedies = [
            'Stay well hydrated throughout the day',
            'Ensure adequate rest and sleep',
            'Maintain a balanced, nutritious diet',
            'Light exercise if feeling up to it'
        ]
    
    return remedies[:3]

def extract_triage_level_whatsapp(text):
    text_lower = text.lower()
    
    urgent_keywords = [
        'chest pain', 'heart attack', 'severe chest pressure', 'difficulty breathing', 'can\'t breathe', 'choking',
        'stroke', 'sudden weakness', 'facial drooping', 'slurred speech', 'severe headache', 'loss of consciousness', 
        'unconscious', 'seizure', 'severe bleeding', 'heavy bleeding', 'broken bone', 'poisoning', 'overdose', 
        'suicide', 'critical', 'dying', 'ambulance needed', 'vomiting blood', 'coughing blood', 'severe allergic reaction'
    ]
    
    semi_urgent_keywords = [
        'persistent fever', 'fever for days', 'high fever', 'severe cough', 'wheezing', 'chest tightness', 
        'persistent vomiting', 'severe diarrhea', 'dehydration', 'moderate pain', 'persistent headache', 
        'migraine', 'infection', 'rash spreading', 'swelling', 'dizziness severe', 'fainting', 'irregular heartbeat',
        'vision problems', 'worsening', 'not improving', 'should see doctor', '24-48 hours'
    ]
    
    if any(keyword in text_lower for keyword in urgent_keywords):
        return 'URGENT'
    elif any(keyword in text_lower for keyword in semi_urgent_keywords):
        return 'SEMI-URGENT'
    else:
        return 'ROUTINE'

def extract_specialty_whatsapp(text):
    text_lower = text.lower()
    
    specialties_map = {
        'cardiologist': 'Cardiologist', 'heart': 'Cardiologist', 
        'neurologist': 'Neurologist', 'brain': 'Neurologist', 'stroke': 'Neurologist',
        'orthopedic': 'Orthopedic Surgeon', 'bone': 'Orthopedic Surgeon', 
        'dermatologist': 'Dermatologist', 'skin': 'Dermatologist', 
        'psychiatrist': 'Psychiatrist', 'mental': 'Psychiatrist', 
        'ophthalmologist': 'Ophthalmologist', 'eye': 'Ophthalmologist', 
        'gastroenterologist': 'Gastroenterologist', 'stomach': 'Gastroenterologist', 
        'dentist': 'Dentist', 
        'general practitioner': 'General Practitioner', 'fever': 'General Practitioner', 'cold': 'General Practitioner'
    }
    
    for keyword, specialty in specialties_map.items():
        if keyword in text_lower:
            return specialty
        
    return 'General Practitioner'

def find_doctors_by_specialty_whatsapp(specialty, user_location):
    try:
        if not specialty or not hasattr(Doctor, 'objects'):
            return []
            
        doctor_list = []
        
        try:
            if hasattr(Category, 'objects'):
                category_obj = Category.objects.get(name__iexact=specialty)
                filters = {'category': category_obj, 'is_available': True}
                
                if user_location and user_location.lower() not in ['skip', 'unknown']:
                    filters['hospital__city__iexact'] = user_location

                doctors = Doctor.objects.filter(**filters).select_related('category', 'hospital').order_by('-experience_years')[:3]
            else:
                doctors = []
        except (Category.DoesNotExist, AttributeError):
            try:
                filters = {'bio__icontains': specialty, 'is_available': True}
                if user_location and user_location.lower() not in ['skip', 'unknown']:
                    filters['hospital__city__iexact'] = user_location
                    
                doctors = Doctor.objects.filter(**filters).select_related('category', 'hospital').order_by('-experience_years')[:3]
            except Exception:
                doctors = []
        
        for doctor in doctors:
            try:
                name = getattr(doctor, 'full_name', 'Unknown Doctor')
                bio = getattr(doctor, 'bio', '')
                category = getattr(doctor, 'category', None)
                hospital = getattr(doctor, 'hospital', None)
                experience = getattr(doctor, 'experience_years', 0)
                
                doctor_data = {
                    'name': name,
                    'specialty': bio or (category.name if category else specialty), 
                    'experience': f"{experience} Years" if experience else 'Experienced',
                    'hospital': hospital.name if hospital else 'Unknown Hospital',
                    'phone': str(hospital.phone) if hospital and hasattr(hospital, 'phone') and hospital.phone else 'N/A'
                }
                doctor_list.append(doctor_data)
            except Exception as doctor_error:
                logger.error(f"Error processing doctor: {str(doctor_error)}")
                continue
        
        return doctor_list
        
    except Exception as e:
        logger.error(f"Error finding doctors: {str(e)}")
        return []

def find_nearby_hospitals_whatsapp(user_location):
    try:
        if not hasattr(Hospital, 'objects'):
            return []
            
        hospitals = Hospital.objects.filter(is_active=True)
        
        if user_location and user_location.lower() not in ['skip', 'unknown']:
            hospitals = hospitals.filter(city__iexact=user_location)
        
        hospital_list = []
        for hospital in hospitals[:3]:
            try:
                name = getattr(hospital, 'name', 'Unknown Hospital')
                address = getattr(hospital, 'address', 'Address not available')
                city = getattr(hospital, 'city', 'City not available')
                phone = getattr(hospital, 'phone', None)
                
                hospital_data = {
                    'name': name,
                    'address': address,
                    'city': city,
                    'phone': str(phone) if phone else 'Contact hospital directly'
                }
                hospital_list.append(hospital_data)
            except Exception as hospital_error:
                logger.error(f"Error processing hospital: {str(hospital_error)}")
                continue
        
        return hospital_list
        
    except Exception as e:
        logger.error(f"Error finding hospitals: {str(e)}")
        return []

def get_emergency_hospitals_whatsapp(user_location):
    return find_nearby_hospitals_whatsapp(user_location)

def format_recommendations_whatsapp(recommendations):
    text = ""
    
    if recommendations.get('doctors'):
        text += "*🩺 Recommended Doctors (Top 2):*\n"
        for doctor in recommendations['doctors'][:2]:
            text += f"\n*Dr. {doctor['name']}* ({doctor['specialty']})\n"
            text += f"🏢 {doctor['hospital']}\n"
            text += f"⏳ Exp: {doctor['experience']}\n"
            if doctor['phone'] != 'N/A' and doctor['phone'] != 'Contact hospital directly':
                text += f"📞 Call: {doctor['phone']}\n"
    
    if recommendations.get('hospitals') and not recommendations.get('doctors'):
          text += "*🏥 Nearby Hospitals (Top 2):*\n"
          for hospital in recommendations['hospitals'][:2]:
              text += f"\n*{hospital['name']}*\n"
              text += f"📍 {hospital['address']}, {hospital['city']}\n"
              if hospital.get('phone') and hospital['phone'] != 'Contact hospital directly':
                  text += f"📞 Phone: {hospital['phone']}\n"
    
    text += "\n---\n"
    
    appointment_url = "https://symptomwise.loca.lt/appointment/"
    text += f"*📅 Book Appointment:* {appointment_url}\n"
    
    if recommendations.get('doctors'):
        text += "_Click the link above to book with recommended doctors_"
    elif recommendations.get('hospitals'):
        text += "_Click the link above to book at nearby hospitals_"
    else:
        text += "_Click the link above to find doctors and book appointments_"
    
    return text

def send_whatsapp_message(to_number, message):
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