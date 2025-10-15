from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from tenants.models import TenantAwareModel
import json

class ChatSession(TenantAwareModel):
    """
    Enhanced chat session with better guest support and history management
    """
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    is_guest = models.BooleanField(default=True)
    
    # Guest session management
    guest_identifier = models.CharField(max_length=100, blank=True, help_text="Browser fingerprint or IP for guests")
    guest_name = models.CharField(max_length=100, blank=True, help_text="Optional name provided by guest")
    guest_email = models.EmailField(blank=True, help_text="Optional email provided by guest")
    
    # Session metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # History settings
    context_days = models.IntegerField(default=10, help_text="Days to keep history for guests")
    max_messages = models.IntegerField(default=100, help_text="Maximum messages to keep")
    
    # Session preferences
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    
    # AI context
    context_summary = models.TextField(blank=True, help_text="AI-generated summary of conversation")
    user_preferences = models.JSONField(default=dict, help_text="User preferences and context")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['guest_identifier', 'is_guest']),
            models.Index(fields=['expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Set expiration for guest sessions
        if self.is_guest and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=self.context_days)
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.is_guest:
            name = self.guest_name or f"Guest-{self.session_id[:8]}"
        else:
            name = self.user.username if self.user else "Unknown User"
        return f"Session {self.session_id} - {name} ({self.hospital.name if self.hospital else 'No Hospital'})"
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_display_name(self):
        if self.is_guest:
            return self.guest_name or "Guest User"
        return self.user.get_full_name() or self.user.username if self.user else "Unknown User"
    
    def cleanup_old_messages(self):
        """Remove old messages beyond the limit"""
        messages = self.messages.order_by('-timestamp')
        if messages.count() > self.max_messages:
            old_messages = messages[self.max_messages:]
            ChatMessage.objects.filter(id__in=[m.id for m in old_messages]).delete()

class ChatMessage(models.Model):
    """
    Enhanced chat message with metadata and context
    """
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')])
    content = models.TextField()
    
    # Message metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    message_type = models.CharField(max_length=30, choices=[
        ('text', 'Text'),
        ('doctor_recommendation', 'Doctor Recommendation'),
        ('appointment_booking', 'Appointment Booking'),
        ('hospital_info', 'Hospital Information'),
        ('symptom_analysis', 'Symptom Analysis'),
        ('emergency_triage', 'Emergency Triage'),
        ('triage_followup', 'Triage Follow-up'),
        ('triage_update', 'Triage Update'),
        ('followup_answers', 'Follow-up Answers'),
    ], default='text')
    
    # AI processing metadata
    processing_time = models.FloatField(null=True, blank=True, help_text="Time taken to generate response")
    model_used = models.CharField(max_length=50, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Structured data (for recommendations, etc.)
    structured_data = models.JSONField(default=dict, help_text="Structured data like doctor recommendations")
    
    # User feedback
    is_helpful = models.BooleanField(null=True, blank=True)
    feedback_text = models.TextField(blank=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['session', 'timestamp']),
            models.Index(fields=['role', 'message_type']),
        ]
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
    
    def get_structured_recommendations(self):
        """Get doctor recommendations from structured data"""
        return self.structured_data.get('doctor_recommendations', [])
    
    def add_doctor_recommendation(self, doctor_data):
        """Add a doctor recommendation to structured data"""
        if 'doctor_recommendations' not in self.structured_data:
            self.structured_data['doctor_recommendations'] = []
        self.structured_data['doctor_recommendations'].append(doctor_data)
        self.save()

class WhatsAppSession(TenantAwareModel):
    """
    WhatsApp integration session
    """
    phone_number = models.CharField(max_length=20)
    chat_session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    
    # WhatsApp specific
    whatsapp_name = models.CharField(max_length=100, blank=True)
    profile_name = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    
    # Settings
    notifications_enabled = models.BooleanField(default=True)
    preferred_language = models.CharField(max_length=10, default='en')
    
    class Meta:
        unique_together = ['hospital', 'phone_number']
        ordering = ['-last_message_at']
    
    def __str__(self):
        name = self.whatsapp_name or self.phone_number
        return f"WhatsApp: {name} ({self.hospital.name if self.hospital else 'No Hospital'})"

class ChatAnalytics(TenantAwareModel):
    """
    Analytics for chat sessions and AI performance
    """
    date = models.DateField()
    
    # Session metrics
    total_sessions = models.IntegerField(default=0)
    guest_sessions = models.IntegerField(default=0)
    user_sessions = models.IntegerField(default=0)
    whatsapp_sessions = models.IntegerField(default=0)
    
    # Message metrics
    total_messages = models.IntegerField(default=0)
    user_messages = models.IntegerField(default=0)
    assistant_messages = models.IntegerField(default=0)
    
    # AI performance
    avg_response_time = models.FloatField(default=0)
    avg_confidence_score = models.FloatField(default=0)
    
    # User satisfaction
    helpful_responses = models.IntegerField(default=0)
    unhelpful_responses = models.IntegerField(default=0)
    
    # Feature usage
    doctor_recommendations = models.IntegerField(default=0)
    appointment_bookings = models.IntegerField(default=0)
    hospital_inquiries = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['hospital', 'date']
        ordering = ['-date']
        verbose_name_plural = "Chat Analytics"
    
    def __str__(self):
        return f"Analytics for {self.date} - {self.hospital.name if self.hospital else 'No Hospital'}"

class UserIntent(models.Model):
    """
    AI training data for user intent recognition
    """
    intent_name = models.CharField(max_length=50)
    description = models.TextField()
    
    # Training examples
    example_phrases = models.JSONField(default=list, help_text="List of example user phrases")
    keywords = models.JSONField(default=list, help_text="Keywords associated with this intent")
    
    # Response templates
    response_templates = models.JSONField(default=list, help_text="Template responses for this intent")
    
    # Metadata
    is_active = models.BooleanField(default=True)
    confidence_threshold = models.FloatField(default=0.7)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['intent_name']
    
    def __str__(self):
        return self.intent_name
    
    def add_example(self, phrase):
        """Add a new example phrase"""
        if phrase not in self.example_phrases:
            self.example_phrases.append(phrase)
            self.save()
