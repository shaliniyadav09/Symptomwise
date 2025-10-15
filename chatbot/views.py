from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import requests
import re
import time
from adminapp.models import Doctor, Category
from tenants.models import Hospital
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import logging
from .models import ChatSession
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "symptomwise"

def get_fallback_response(user_message):
    """Provide structured fallback response when AI service is unavailable"""
    try:
        user_lower = user_message.lower() if user_message else ""
        
        # Emergency keywords
        emergency_keywords = [
            'chest pain', 'heart attack', 'stroke', 'difficulty breathing', 
            'severe pain', 'bleeding', 'unconscious', 'emergency'
        ]
        
        if any(keyword in user_lower for keyword in emergency_keywords):
            return "EMERGENCY DETECTED: Please call 108 immediately for emergency medical services. If you're experiencing severe symptoms, don't wait - seek immediate medical attention at the nearest hospital emergency room."
        
        # Common symptoms with structured advice
        if 'headache' in user_lower:
            return "I understand you're experiencing a headache. Here's what I can suggest:"
        
        elif 'fever' in user_lower:
            return "I see you have a fever. Let me provide some guidance:"
        
        elif 'cough' in user_lower:
            return "I understand you have a cough. Here are some recommendations:"
        
        elif 'dizzy' in user_lower or 'dizziness' in user_lower:
            return "I'm sorry to hear that. It's possible you have low blood pressure or a problem with your inner ear. To help you better, could you please tell me what other symptoms you are feeling along with this?"
        
        elif any(word in user_lower for word in ['stomach', 'nausea', 'vomiting']):
            return "I understand you're having stomach issues. Here's what might help:"
        
        elif 'appointment' in user_lower or 'book' in user_lower:
            return "I can help you book an appointment with our healthcare professionals. Let me show you available options:"
        
        elif any(word in user_lower for word in ['better', 'fine', 'okay', 'good']):
            return "That's wonderful to hear! I'm glad you're feeling better."
        
        else:
            return "I'm here to help with your health concerns. Please describe your symptoms and I'll provide appropriate guidance and recommendations."
    except Exception as e:
        logger.error(f"Error in get_fallback_response: {str(e)}")
        return "I'm here to help with your health concerns. Please describe your symptoms and I'll provide appropriate guidance and recommendations."

def chatbot_page(request):
    """Render the chatbot page"""
    return render(request, 'chatbot/chat.html')

@csrf_exempt
def chat_stream(request):
    """Handle streaming chat responses with improved session management"""
    # Handle GET requests (invalid for this endpoint)
    if request.method == 'GET':
        return JsonResponse({
            'error': 'This endpoint only accepts POST requests for chat messages'
        }, status=405)
    
    # Handle POST requests
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        user_location = data.get('location', {})
        session_id = data.get('session_id')
        is_guest = data.get('is_guest', True)
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get stored location if not provided
        if not user_location and session_id:
            if is_guest:
                user_location = request.session.get(f'guest_location_{session_id}', {})
            else:
                user_location = request.session.get('user_location', {})
        
        # Generate streaming response
        def generate_response():
            try:
                # Call Ollama API
                payload = {
                    "model": MODEL_NAME,
                    "prompt": user_message,
                    "stream": True
                }
                
                # Try to connect to Ollama API with timeout
                try:
                    response = requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=10)
                    
                    if response.status_code != 200:
                        logger.warning(f"Ollama API returned status {response.status_code}")
                        yield f"data: {json.dumps({'error': 'AI service temporarily unavailable', 'fallback_response': get_fallback_response(user_message)})}\\n\\n"
                        return
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Ollama API connection failed: {str(e)}")
                    # Provide fallback response when Ollama is not available
                    fallback_response = get_fallback_response(user_message)
                    yield f"data: {json.dumps({'token': fallback_response, 'fallback': True})}\\n\\n"
                    
                    # Process fallback response for recommendations
                    conversation_stage = request.session.get('conversation_stage', 'initial')
                    recommendations = process_medical_response(fallback_response, user_location, user_message, conversation_stage)
                    request.session['conversation_stage'] = recommendations.get('conversation_stage', 'initial')
                    yield f"data: {json.dumps({'recommendations': recommendations, 'done': True})}\\n\\n"
                    return
                
                full_response = ""
                
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if 'response' in chunk:
                                token = chunk['response']
                                full_response += token
                                
                                # Send token to frontend
                                yield f"data: {json.dumps({'token': token})}\\n\\n"
                                
                                # Add small delay for animation effect
                                time.sleep(0.02)
                                
                            if chunk.get('done', False):
                                # Get conversation stage from session
                                conversation_stage = request.session.get('conversation_stage', 'initial')
                                
                                # Process the complete response for medical recommendations
                                recommendations = process_medical_response(full_response, user_location, user_message, conversation_stage)
                                
                                # Update conversation stage in session
                                request.session['conversation_stage'] = recommendations.get('conversation_stage', 'initial')
                                
                                yield f"data: {json.dumps({'recommendations': recommendations, 'done': True})}\\n\\n"
                                break
                                
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"Error in chat stream: {str(e)}")
                # Provide fallback response on any error
                fallback_response = get_fallback_response(user_message)
                yield f"data: {json.dumps({'error': 'Service temporarily unavailable', 'fallback_response': fallback_response})}\\n\\n"
        
        return StreamingHttpResponse(
            generate_response(),
            content_type='text/event-stream'
        )
        
    except Exception as e:
        logger.error(f"Error in chat_stream: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_user_location(request):
    """Get user's location for nearby hospital search with session management"""
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        session_id = data.get('session_id')
        is_guest = data.get('is_guest', True)
        accuracy = data.get('accuracy')
        timestamp = data.get('timestamp')
        
        if not latitude or not longitude:
            return JsonResponse({'error': 'Invalid location data'}, status=400)
        
        # Create location data
        location_data = {
            'latitude': latitude,
            'longitude': longitude,
            'accuracy': accuracy,
            'timestamp': timestamp or time.time(),
            'session_id': session_id,
            'is_guest': is_guest
        }
        
        # Store location in session
        request.session['user_location'] = location_data
        
        # For guests, also store in a more persistent way
        if is_guest and session_id:
            # Store in session with guest session ID as key
            request.session[f'guest_location_{session_id}'] = location_data
        
        # Try to get or create chat session for better tracking
        try:
            if is_guest:
                # Handle guest session
                chat_session, created = ChatSession.objects.get_or_create(
                    session_id=session_id,
                    defaults={
                        'is_guest': True,
                        'guest_identifier': request.META.get('REMOTE_ADDR', ''),
                        'user_preferences': {'location': location_data}
                    }
                )
                if not created:
                    # Update existing session with new location
                    chat_session.user_preferences['location'] = location_data
                    chat_session.save()
            else:
                # Handle authenticated user session
                if request.user.is_authenticated:
                    chat_session, created = ChatSession.objects.get_or_create(
                        user=request.user,
                        is_guest=False,
                        defaults={
                            'session_id': session_id or f'user_{request.user.id}_{int(time.time())}',
                            'user_preferences': {'location': location_data}
                        }
                    )
                    if not created:
                        chat_session.user_preferences['location'] = location_data
                        chat_session.save()
        except Exception as db_error:
            logger.warning(f"Could not save to database: {str(db_error)}")
            # Continue without database save - session storage is still working
        
        logger.info(f"Location stored for session {session_id} (guest: {is_guest}): {latitude}, {longitude}")
        return JsonResponse({
            'success': True,
            'message': 'Location stored successfully',
            'session_id': session_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error storing location: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

# Copy all the other functions from the original views.py
def process_medical_response(response_text, user_location, user_message="", conversation_stage="initial"):
    """Process the AI response and extract medical recommendations with structured output"""
    # Check if user is feeling better first - this should reset the conversation
    feeling_better_keywords = [
    'feel better', 'feeling better', 'i\'m better', 'better now', 'i feel better',
    'feeling fine', 'i\'m fine', 'fine now', 'okay now', 'i am okay',
    'resolved', 'no longer', 'not anymore', 'symptoms gone', 'much better',
    'all good', 'recovered', 'back to normal', 'no more symptoms'
]
    
    user_lower = user_message.lower()
    is_feeling_better = any(keyword in user_lower for keyword in feeling_better_keywords)
    
    # If user is feeling better, reset conversation and provide fresh greeting
    if is_feeling_better:
        return {
            'specialty': None,
            'triage': None,
            'doctors': [],
            'hospitals': [],
            'youtube_links': [],
            'first_aid_link': None,
            'is_emergency': False,
            'emergency_message': None,
            'remedies': [],
            'show_appointment_option': False,
            'conversation_stage': 'initial',
            'feeling_better': True,
            'reset_conversation': True
        }
    
    # Check for emergency keywords
    emergency_keywords = [
        'bleeding', 'blood', 'chest pain', 'heart attack', 'stroke', 'unconscious',
        'difficulty breathing', 'severe pain', 'accident', 'injury', 'broken bone',
        'head injury', 'poisoning', 'overdose', 'suicide', 'emergency', 'urgent',
        'severe', 'critical', 'dying', 'death', 'ambulance', 'hospital now'
    ]
    
    is_emergency = any(keyword in user_message.lower() for keyword in emergency_keywords)
    
    recommendations = {
        'specialty': None,
        'triage': None,
        'doctors': [],
        'hospitals': [],
        'youtube_links': [],
        'first_aid_link': None,
        'is_emergency': is_emergency,
        'emergency_message': None,
        'remedies': [],
        'show_appointment_option': False,
        'conversation_stage': conversation_stage
    }
    
    try:
        # Handle emergency cases first
        if is_emergency:
            recommendations['emergency_message'] = "⚠️ EMERGENCY DETECTED ⚠️\n\n🚨 CALL 108 IMMEDIATELY FOR EMERGENCY SERVICES! 🚨\n\nDo not wait - seek immediate medical attention at the nearest hospital emergency room.\n\n🏥 Nearby Emergency Hospitals:"
            recommendations['triage'] = 'URGENT'
            recommendations['warning_level'] = 'DANGER'
            recommendations['urgent_action'] = 'Call 108 now and go to nearest emergency room'
            
            # Get emergency hospitals with phone numbers
            emergency_hospitals = get_emergency_hospitals(user_location)
            recommendations['hospitals'] = emergency_hospitals
            
            return recommendations
        
        # Check if user wants to book appointment
        appointment_keywords = ['book appointment', 'schedule appointment', 'see doctor', 'visit doctor', 'appointment', 'yes book', 'yes schedule']
        wants_appointment = any(keyword in user_message.lower() for keyword in appointment_keywords)
        
        if conversation_stage == "initial" and not wants_appointment:
            # Check urgency level first
            triage = extract_triage_level(response_text + " " + user_message)
            recommendations['triage'] = triage
            
            if triage == 'URGENT':
                # URGENT: Show emergency message, call 108, show hospitals
                recommendations['warning_level'] = 'DANGER'
                recommendations['urgent_message'] = "🚨 URGENT: Your symptoms require IMMEDIATE medical attention!\n\n📞 Call 108 for emergency services or go to the nearest emergency room NOW."
                recommendations['urgent_action'] = 'Call 108 immediately'
                
                # Show emergency hospitals
                emergency_hospitals = get_emergency_hospitals(user_location)
                recommendations['hospitals'] = emergency_hospitals
                recommendations['conversation_stage'] = 'emergency_shown'
                
            elif triage == 'SEMI-URGENT':
                # SEMI-URGENT: Show warning, suggest 24-48 hours, show doctors and hospitals
                recommendations['warning_level'] = 'WARNING'
                recommendations['urgent_message'] = "⚠️ SEMI-URGENT: Your symptoms should be evaluated by a healthcare professional within 24-48 hours.\n\nPlease schedule an appointment or visit a clinic soon."
                recommendations['urgent_action'] = 'See a doctor within 24-48 hours'
                
                # Show doctors and hospitals
                specialty = extract_specialty(response_text + " " + user_message)
                if specialty:
                    recommendations['specialty'] = specialty
                    doctors = find_doctors_by_specialty(specialty, user_location)
                    recommendations['doctors'] = doctors
                
                hospitals = find_nearby_hospitals(user_location)
                recommendations['hospitals'] = hospitals
                recommendations['show_appointment_option'] = True
                recommendations['conversation_stage'] = 'semi_urgent_shown'
                
            else:
                # ROUTINE: Show remedies only, with appointment option
                recommendations['warning_level'] = 'INFO'
                recommendations['routine_message'] = "ℹ️ ROUTINE: These symptoms can typically be managed with home care and self-treatment."
                
                # Show home remedies
                remedies = extract_remedies(response_text, user_message)
                recommendations['remedies'] = remedies
                recommendations['show_appointment_option'] = True
                recommendations['conversation_stage'] = 'remedies_shown'
                
                # Show hospitals for reference but don't emphasize urgency
                hospitals = find_nearby_hospitals(user_location)
                recommendations['hospitals'] = hospitals
            
            # Get YouTube links for the condition (for all triage levels)
            youtube_links = search_youtube_videos(response_text)
            recommendations['youtube_links'] = youtube_links
            
        elif wants_appointment or conversation_stage == "appointment_requested":
            # User wants appointment - show doctors and hospitals
            specialty = extract_specialty(response_text + " " + user_message)
            if specialty:
                recommendations['specialty'] = specialty
                doctors = find_doctors_by_specialty(specialty, user_location)
                recommendations['doctors'] = doctors
            else:
                # If no specific specialty, show general practitioners
                doctors = find_doctors_by_specialty('General Practitioner', user_location)
                recommendations['doctors'] = doctors
            
            # Extract triage level
            triage = extract_triage_level(response_text + " " + user_message)
            recommendations['triage'] = triage
            
            # Find nearby hospitals
            hospitals = find_nearby_hospitals(user_location)
            recommendations['hospitals'] = hospitals
            recommendations['conversation_stage'] = 'appointment_options_shown'
            
    except Exception as e:
        logger.error(f"Error processing medical response: {str(e)}")
    
    return recommendations

# Include all other functions from the original views.py
def extract_remedies(response_text, user_message):
    """Extract home remedies and self-care tips from AI response"""
    remedies = []
    
    # Common remedy patterns
    remedy_keywords = {
        'headache': [
            ' Stay hydrated - drink plenty of water',
            ' Get adequate rest in a dark, quiet room',
            ' Apply cold compress to forehead',
            ' Try herbal teas like peppermint or ginger'
        ],
        'fever': [
            ' Monitor temperature regularly',
            ' Increase fluid intake',
            ' Get plenty of rest',
            ' Use lukewarm sponge baths to cool down'
        ],
        'cough': [
            ' Honey and warm water can soothe throat',
            ' Use a humidifier or steam inhalation',
            ' Drink warm herbal teas',
            ' Avoid irritants like smoke'
        ],
        'cold': [
            ' Stay well hydrated',
            ' Gargle with warm salt water',
            ' Get extra sleep and rest',
            ' Eat warm, nutritious soups'
        ],
        'stomach': [
            ' Try ginger tea for nausea',
            ' Eat bland foods like bananas and rice',
            ' Stay hydrated with small sips',
            ' Rest and avoid heavy meals'
        ],
        'dizzy': [
            ' Stay well hydrated throughout the day',
            ' Ensure adequate rest and sleep',
            ' Maintain a balanced, nutritious diet',
            ' Light exercise if feeling up to it'
        ],
        'dizziness': [
            ' Stay well hydrated throughout the day',
            ' Ensure adequate rest and sleep',
            ' Maintain a balanced, nutritious diet',
            ' Light exercise if feeling up to it'
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
            '💧 Stay well hydrated throughout the day',
            '😴 Ensure adequate rest and sleep',
            '🍎 Maintain a balanced, nutritious diet',
            '🏃‍♂️ Light exercise if feeling up to it'
        ]
    
    return remedies[:4]  # Return max 4 remedies

def extract_specialty(text):
    """Extract recommended medical specialty from AI response"""
    specialties_map = {
        'cardiologist': 'Cardiologist',
        'cardiology': 'Cardiologist', 
        'heart': 'Cardiologist',
        'cardiac': 'Cardiologist',
        'chest pain': 'Cardiologist',
        'neurologist': 'Neurologist',
        'neurology': 'Neurologist',
        'brain': 'Neurologist',
        'nervous': 'Neurologist',
        'headache': 'Neurologist',
        'migraine': 'Neurologist',
        'dizziness': 'Neurologist',
        'seizure': 'Neurologist',
        'orthopedic': 'Orthopedic Surgeon',
        'orthopedist': 'Orthopedic Surgeon',
        'bone': 'Orthopedic Surgeon',
        'joint': 'Orthopedic Surgeon',
        'fracture': 'Orthopedic Surgeon',
        'back pain': 'Orthopedic Surgeon',
        'knee pain': 'Orthopedic Surgeon',
        'dermatologist': 'Dermatologist',
        'dermatology': 'Dermatologist',
        'skin': 'Dermatologist',
        'rash': 'Dermatologist',
        'acne': 'Dermatologist',
        'eczema': 'Dermatologist',
        'psychiatrist': 'Psychiatrist',
        'psychiatry': 'Psychiatrist',
        'mental': 'Psychiatrist',
        'depression': 'Psychiatrist',
        'anxiety': 'Psychiatrist',
        'stress': 'Psychiatrist',
        'ophthalmologist': 'Ophthalmologist',
        'ophthalmology': 'Ophthalmologist',
        'eye': 'Ophthalmologist',
        'vision': 'Ophthalmologist',
        'blurred vision': 'Ophthalmologist',
        'general practitioner': 'General Practitioner',
        'gp': 'General Practitioner',
        'family doctor': 'General Practitioner',
        'fever': 'General Practitioner',
        'cold': 'General Practitioner',
        'flu': 'General Practitioner',
        'cough': 'General Practitioner'
    }
    
    text_lower = text.lower()
    for keyword, specialty in specialties_map.items():
        if keyword in text_lower:
            return specialty
    
    return None

def extract_triage_level(text):
    """Enhanced triage level extraction with comprehensive symptom analysis"""
    text_lower = text.lower()
    
    # URGENT/EMERGENCY symptoms - Require immediate medical attention
    urgent_keywords = [
        # Cardiovascular emergencies
        'chest pain', 'heart attack', 'cardiac arrest', 'severe chest pressure',
        'crushing chest pain', 'radiating arm pain', 'jaw pain with chest',
        
        # Respiratory emergencies
        'difficulty breathing', 'can\'t breathe', 'choking', 'gasping for air',
        'severe shortness of breath', 'blue lips', 'blue fingernails',
        
        # Neurological emergencies
        'stroke', 'sudden weakness', 'facial drooping', 'slurred speech',
        'severe headache', 'worst headache ever', 'sudden confusion',
        'loss of consciousness', 'unconscious', 'seizure', 'convulsions',
        
        # Trauma and bleeding
        'severe bleeding', 'heavy bleeding', 'bleeding heavily', 'hemorrhage',
        'head injury', 'broken bone', 'compound fracture', 'severe trauma',
        
        # Poisoning and overdose
        'poisoning', 'overdose', 'toxic', 'swallowed poison',
        
        # Severe pain
        'severe pain', 'excruciating pain', 'unbearable pain', '10/10 pain',
        'severe abdominal pain', 'appendicitis symptoms',
        
        # Other emergencies
        'suicide', 'suicidal thoughts', 'want to die', 'emergency',
        'critical', 'dying', 'life threatening', 'ambulance needed',
        'vomiting blood', 'coughing blood', 'blood in stool',
        'severe allergic reaction', 'anaphylaxis', 'swollen throat'
    ]
    
    # SEMI-URGENT symptoms - Need medical attention within 24-48 hours
    semi_urgent_keywords = [
        # Persistent symptoms
        'persistent fever', 'fever for days', 'high fever', 'fever above 102',
        'persistent vomiting', 'vomiting for hours', 'severe nausea',
        'persistent diarrhea', 'severe diarrhea', 'dehydration',
        
        # Respiratory issues
        'severe cough', 'coughing for weeks', 'shortness of breath',
        'wheezing', 'chest tightness',
        
        # Pain and discomfort
        'moderate pain', 'persistent headache', 'severe headache',
        'migraine', 'back pain severe', 'joint pain severe',
        
        # Infections and inflammation
        'infection', 'infected wound', 'rash spreading', 'severe rash',
        'swelling', 'inflammation', 'red streaks', 'pus',
        
        # Digestive issues
        'severe stomach pain', 'abdominal pain', 'difficulty swallowing',
        'blood in urine', 'painful urination',
        
        # Mental health urgent
        'severe depression', 'panic attacks', 'severe anxiety',
        
        # Other semi-urgent
        'dizziness severe', 'fainting', 'irregular heartbeat',
        'vision problems', 'sudden vision loss', 'eye injury',
        'worsening', 'getting worse', 'not improving',
        'need to see doctor', 'should see doctor', '24-48 hours'
    ]
    
    # Check for urgent symptoms first
    if any(keyword in text_lower for keyword in urgent_keywords):
        return 'URGENT'
    elif any(keyword in text_lower for keyword in semi_urgent_keywords):
        return 'SEMI-URGENT'
    else:
        return 'ROUTINE'

def find_doctors_by_specialty(specialty, user_location):
    """Find doctors matching the specialty with safe JSON serialization"""
    try:
        # Find doctors with matching bio or category
        doctors = Doctor.objects.filter(
            bio__icontains=specialty,
            is_available=True
        ).select_related('category', 'hospital')[:5]
        
        if not doctors:
            # Try to find by category name
            doctors = Doctor.objects.filter(
                category__name__icontains=specialty,
                is_available=True
            ).select_related('category', 'hospital')[:5]
        
        doctor_list = []
        for doctor in doctors:
            try:
                # Safe field access with proper type conversion
                doctor_data = {
                    'id': doctor.id,
                    'name': doctor.full_name,
                    'specialty': doctor.bio or (doctor.category.name if doctor.category else 'General Medicine'),
                    'experience': f"{doctor.experience_years} Years" if hasattr(doctor, 'experience_years') and doctor.experience_years else 'Experienced',
                    'hospital': doctor.hospital.name if doctor.hospital else 'Unknown Hospital',
                    'consultation_fee': float(doctor.consultation_fee) if doctor.consultation_fee else 500.0,
                    'image': doctor.profile_image.url if doctor.profile_image else None
                }
                doctor_list.append(doctor_data)
            except Exception as doctor_error:
                logger.error(f"Error processing doctor {doctor.id}: {str(doctor_error)}")
                # Skip this doctor and continue with others
                continue
        
        return doctor_list
        
    except Exception as e:
        logger.error(f"Error finding doctors: {str(e)}")
        return []

def get_emergency_hospitals(user_location):
    """Get hospitals with emergency contact info"""
    try:
        hospitals = Hospital.objects.filter(is_active=True)[:3]  # Top 3 for emergency
        
        hospital_list = []
        for hospital in hospitals:
            try:
                # Safe field access with proper type conversion
                hospital_data = {
                    'id': str(hospital.id),
                    'name': hospital.name,
                    'address': hospital.address,
                    'city': hospital.city,
                    'state': hospital.state,
                    'phone': str(hospital.phone) if hospital.phone else 'Contact hospital directly',
                    'website': hospital.website if hospital.website else '',
                    'emergency': True
                }
                hospital_list.append(hospital_data)
            except Exception as hospital_error:
                logger.error(f"Error processing hospital {hospital.id}: {str(hospital_error)}")
                continue
        
        return hospital_list
        
    except Exception as e:
        logger.error(f"Error finding emergency hospitals: {str(e)}")
        return []

def find_nearby_hospitals(user_location):
    """Find hospitals near user location"""
    try:
        hospitals = Hospital.objects.filter(is_active=True)
        
        hospital_list = []
        for hospital in hospitals:
            try:
                # Safe field access with proper type conversion
                hospital_data = {
                    'id': str(hospital.id),
                    'name': hospital.name,
                    'address': hospital.address,
                    'city': hospital.city,
                    'state': hospital.state,
                    'phone': str(hospital.phone) if hospital.phone else 'Contact hospital directly',
                    'website': hospital.website if hospital.website else '',
                    'distance': 0  # Default distance
                }
                
                # Simple location-based sorting (prioritize hospitals with 'JP' in name if user location available)
                if user_location and 'latitude' in user_location:
                    # Prioritize JP Hospital if it exists
                    if 'jp' in hospital.name.lower() or 'jp hospital' in hospital.name.lower():
                        hospital_data['distance'] = -1  # Negative to sort first
                    else:
                        hospital_data['distance'] = 1
                
                hospital_list.append(hospital_data)
            except Exception as hospital_error:
                logger.error(f"Error processing hospital {hospital.id}: {str(hospital_error)}")
                continue
        
        # Sort by distance (JP hospitals first if location enabled)
        if user_location and 'latitude' in user_location:
            hospital_list.sort(key=lambda x: x['distance'])
        
        return hospital_list[:5]  # Return top 5
        
    except Exception as e:
        logger.error(f"Error finding hospitals: {str(e)}")
        return []

def search_youtube_videos(text):
    """Search for relevant YouTube videos based on symptoms/condition"""
    try:
        # Extract keywords from the response
        keywords = extract_medical_keywords(text)
        
        if not keywords:
            return []
        
        # For demo purposes, return some sample medical education videos
        # In production, you would use YouTube API
        sample_videos = [
            {
                'title': f'Understanding {keywords[0]} - Medical Education',
                'url': f'https://www.youtube.com/results?search_query={keywords[0]}+medical+education',
                'description': f'Educational video about {keywords[0]}'
            },
            {
                'title': f'{keywords[0]} Treatment Options',
                'url': f'https://www.youtube.com/results?search_query={keywords[0]}+treatment+options',
                'description': f'Treatment information for {keywords[0]}'
            }
        ]
        
        return sample_videos[:2]  # Return max 2 videos
        
    except Exception as e:
        logger.error(f"Error searching YouTube: {str(e)}")
        return []

def extract_medical_keywords(text):
    """Extract medical keywords from text"""
    # Simple keyword extraction - in production, use NLP
    medical_terms = [
        'headache', 'fever', 'cough', 'chest pain', 'back pain',
        'diabetes', 'hypertension', 'asthma', 'arthritis', 'depression',
        'anxiety', 'migraine', 'allergies', 'infection', 'inflammation'
    ]
    
    found_keywords = []
    text_lower = text.lower()
    
    for term in medical_terms:
        if term in text_lower:
            found_keywords.append(term)
    
    return found_keywords

@require_http_methods(["GET"])
def get_all_hospitals(request):
    """Get all hospitals for browsing"""
    try:
        hospitals = Hospital.objects.filter(is_active=True)
        
        hospital_list = []
        for hospital in hospitals:
            try:
                # Safe field access with proper type conversion
                hospital_data = {
                    'id': str(hospital.id),
                    'name': hospital.name,
                    'address': hospital.address,
                    'city': hospital.city,
                    'state': hospital.state,
                    'phone': str(hospital.phone) if hospital.phone else 'Contact hospital directly',
                    'website': hospital.website if hospital.website else '',
                    'email': hospital.email if hospital.email else ''
                }
                hospital_list.append(hospital_data)
            except Exception as hospital_error:
                logger.error(f"Error processing hospital {hospital.id}: {str(hospital_error)}")
                continue
        
        return JsonResponse({'hospitals': hospital_list})
        
    except Exception as e:
        logger.error(f"Error getting hospitals: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)