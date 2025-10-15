
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from .models import ChatSession, ChatMessage
import json
import ollama
import uuid
import time

def chat_interface(request):
    """Simple chat interface with fixed session handling"""
    session = None  # Initialize session variable
    
    # Get or create session
    if request.user.is_authenticated:
        existing_session = ChatSession.objects.filter(
            user=request.user, 
            is_active=True,
            is_guest=False
        ).first()
        
        if existing_session:
            session = existing_session
        else:
            session_id = f"user_{request.user.id}_{uuid.uuid4().hex[:8]}"
            session = ChatSession.objects.create(
                session_id=session_id,
                user=request.user,
                is_guest=False,
                context_days=30
            )
    else:
        guest_session_id = request.session.get('chat_session_id')
        if guest_session_id:
            try:
                session = ChatSession.objects.get(
                    session_id=guest_session_id,
                    is_guest=True,
                    is_active=True
                )
                if session.is_expired:
                    session.is_active = False
                    session.save()
                    session = None  # Reset to create new session
            except ChatSession.DoesNotExist:
                session = None
        
        if not session:
            session_id = f"guest_{uuid.uuid4().hex[:8]}"
            guest_identifier = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
            
            session = ChatSession.objects.create(
                session_id=session_id,
                is_guest=True,
                context_days=10,
                guest_identifier=guest_identifier
            )
            request.session['chat_session_id'] = session_id
    
    # Get messages for this session
    chat_messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
    
    context = {
        'session': session,
        'messages': chat_messages,
        'is_guest': session.is_guest,
        'user_name': session.get_display_name(),
    }
    
    return render(request, 'chatbot/chat.html', context)

@csrf_exempt
def send_message_clean(request):
    """Clean message processing - no interference with your SymptomWise model"""
    if request.method == 'POST':
        start_time = time.time()
        
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id')
            message = data.get('message')
            
            if not session_id or not message:
                return JsonResponse({'error': 'Missing session_id or message'}, status=400)
            
            session = get_object_or_404(ChatSession, session_id=session_id)
            
            # Update session activity
            session.last_activity = timezone.now()
            session.save()
            
            # Save user message
            user_message = ChatMessage.objects.create(
                session=session,
                role='user',
                content=message
            )
            
            # Call your SymptomWise model directly - NO INTERFERENCE
            try:
                # First check if Ollama is running
                import requests
                try:
                    requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2)
                except:
                    raise Exception("Ollama server is not running. Please start it with 'ollama serve'")
                
                # Simple, clean call to your model
                response = ollama.chat(
                    model=settings.OLLAMA_MODEL_NAME,
                    messages=[
                        {"role": "user", "content": message}
                    ],
                    options={
                        'temperature': 0.1,  # Adjust if needed
                        'num_ctx': 4096,
                        'num_predict': 1024
                    }
                )
                
                bot_response = response['message']['content']
                processing_time = time.time() - start_time
                
                # Save bot response
                assistant_message = ChatMessage.objects.create(
                    session=session,
                    role='assistant',
                    content=bot_response,
                    message_type='text',
                    processing_time=processing_time,
                    model_used=settings.OLLAMA_MODEL_NAME
                )
                
                # Clean response - exactly what your model returns
                response_data = {
                    'reply': bot_response,
                    'message_type': 'text',
                    'processing_time': round(processing_time, 2),
                    'session_info': {
                        'is_guest': session.is_guest
                    }
                }
                
                return JsonResponse(response_data)
                
            except Exception as e:
                # Simple fallback
                fallback_response = "I'm having technical difficulties. Please try again."
                
                ChatMessage.objects.create(
                    session=session,
                    role='assistant',
                    content=fallback_response,
                    message_type='text',
                    structured_data={'error': str(e), 'fallback': True}
                )
                
                return JsonResponse({
                    'reply': fallback_response,
                    'message_type': 'text',
                    'is_fallback': True
                })
                
        except Exception as e:
            return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)
