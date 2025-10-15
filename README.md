# 🏥 SymptomWise

A comprehensive multi-tenant hospital management system with AI-powered medical chatbot, appointment booking, and WhatsApp integration.

## 🌟 Features

### 🤖 AI Medical Assistant (SymptomWise)
- **Intelligent Symptom Analysis**: AI-powered chatbot using BioMistral-7B model for medical consultations
- **Emergency Detection**: Automatic detection of emergency symptoms with immediate 108 call recommendations
- **Triage System**: Smart categorization of symptoms into URGENT, SEMI-URGENT, and ROUTINE
- **Doctor Recommendations**: Specialty-based doctor suggestions based on symptoms
- **WhatsApp Integration**: Medical consultations via WhatsApp using Twilio
- **Multi-language Support**: Configurable language preferences

### 🏥 Multi-Tenant Hospital Management
- **Hospital Registration**: Complete hospital onboarding with branding customization
- **Subdomain Support**: Each hospital gets its own subdomain (e.g., apollo.yourdomain.com)
- **Custom Branding**: Hospital-specific logos, colors, and themes
- **Working Hours Management**: Flexible scheduling configuration
- **Subscription Plans**: Trial, Basic, Premium, and Enterprise tiers

### 👨‍⚕️ Doctor & Staff Management
- **Doctor Profiles**: Comprehensive doctor information with specialties and experience
- **Category Management**: Medical specialties and department organization
- **Availability Tracking**: Real-time doctor availability status
- **Multi-hospital Support**: Doctors can be associated with multiple hospitals

### 📅 Appointment System
- **Online Booking**: Patient-friendly appointment scheduling interface
- **Real-time Availability**: Live doctor schedule integration
- **Automated Notifications**: Email and SMS confirmations
- **Guest Booking**: Appointment booking without registration

### 🔐 Authentication & Security
- **Multi-role Access**: Owner, Admin, Manager, Doctor, Receptionist, Staff roles
- **Google OAuth Integration**: Seamless social login
- **Django Allauth**: Comprehensive authentication system
- **CSRF Protection**: Enhanced security measures
- **Session Management**: Secure session handling

### 📊 Analytics & Reporting
- **Chat Analytics**: AI performance metrics and user satisfaction tracking
- **Session Management**: Detailed conversation history and context
- **User Intent Recognition**: AI training data for improved responses
- **Performance Monitoring**: Response times and confidence scores

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 5.2.5
- **Database**: SQLite3 (development) / PostgreSQL (production ready)
- **AI Model**: BioMistral-7B via Ollama
- **Authentication**: Django Allauth with Google OAuth
- **File Storage**: Django's file handling with Pillow for images

### Frontend
- **Templates**: Django Templates with Bootstrap
- **JavaScript**: Vanilla JS with modern ES6+ features
- **CSS**: Custom styling with responsive design
- **Real-time**: Server-Sent Events (SSE) for chat streaming

### Integrations
- **WhatsApp**: Twilio WhatsApp Business API
- **Email**: SMTP with Gmail integration
- **Maps**: Geolocation services for hospital finding
- **AI**: Ollama local AI server

### DevOps & Deployment
- **Static Files**: Django's collectstatic with WhiteNoise ready
- **Media Handling**: Organized media file structure
- **Environment**: Environment variable configuration
- **CORS**: Cross-origin resource sharing support

## 📁 Project Structure

```
Appointment/
├── 🏥 adminapp/              # Hospital admin interface
│   ├── management/           # Custom Django commands
│   ├── static/admin/         # Admin panel assets
│   ├── templates/adminapp/   # Admin templates
│   └── models.py            # Admin models (Doctor, Category)
├── 🏢 Appointment/          # Main Django project
│   ├── settings.py          # Configuration settings
│   ├── urls.py             # URL routing
│   └── wsgi.py             # WSGI configuration
├── 🤖 chatbot/              # AI Medical Assistant
│   ├── models.py           # Chat sessions, messages, analytics
│   ├── views.py            # Chat API endpoints
│   ├── whatsapp_views.py   # WhatsApp integration
│   └── templates/chatbot/  # Chat interface
├── 🏥 hospitals/            # Hospital management
│   ├── models.py           # Hospital services, facilities, contacts
│   ├── views.py            # Hospital CRUD operations
│   └── templates/hospitals/ # Hospital templates
├── 📱 myapp/               # Core application
│   ├── models.py           # User info, enquiries, appointments
│   ├── views.py            # Main application views
│   ├── forms.py            # Django forms
│   ├── validators.py       # Custom validators
│   └── templates/          # Core templates
├── 🏢 tenants/             # Multi-tenancy system
│   ├── models.py           # Hospital, tenant-aware models
│   ├── middleware.py       # Tenant detection middleware
│   └── management/         # Tenant management commands
├── 👤 userapp/             # User management
├── 📁 media/               # User uploaded files
│   ├── doctor_profiles/    # Doctor profile images
│   ├── hospital_logos/     # Hospital branding
│   └── book_covers/        # Miscellaneous uploads
├── 📁 static/              # Static assets
├── 📁 templates/           # Global templates
├── 🤖 Modelfile            # Ollama AI model configuration
├── 📋 requirements.txt     # Python dependencies
└── 🔧 manage.py           # Django management script
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama (for AI features)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Flashyrs/Symptomwise
   cd symptomwise
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Ollama AI Model**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Create the SymptomWise model
   ollama create symptomwise -f Modelfile
   ```

5. **Configure environment variables**
   ```bash
   # Create .env file with your configurations
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

Visit `http://localhost:8000` to access the application.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost:5432/hospital_db

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Google OAuth
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret

# Ollama AI
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=symptomwise
```

### AI Model Configuration

The system uses BioMistral-7B, a specialized medical AI model. The `Modelfile` contains:
- Model parameters (temperature, context window)
- Medical system prompt with emergency detection
- Triage guidelines and specialty recommendations

## 🔧 Key Features Explained

### 1. Multi-Tenant Architecture
Each hospital operates as an independent tenant with:
- Isolated data and users
- Custom branding and configuration
- Subdomain-based access
- Role-based permissions

### 2. AI Medical Assistant
- **Emergency Detection**: Automatically identifies critical symptoms
- **Symptom Triage**: Categorizes urgency levels
- **Doctor Matching**: Recommends specialists based on symptoms
- **Conversation Context**: Maintains chat history and context

### 3. WhatsApp Integration
- Seamless medical consultations via WhatsApp
- Session management across platforms
- Automated responses and appointment booking

### 4. Appointment System
- Real-time doctor availability
- Multi-step booking process
- Email/SMS confirmations
- Guest and registered user support

## 📱 API Endpoints

### Chat API
- `POST /chatbot/chat/` - Send chat message
- `POST /chatbot/location/` - Store user location
- `GET /chatbot/hospitals/` - Get all hospitals

### WhatsApp API
- `POST /chatbot/whatsapp/` - WhatsApp webhook
- `GET /chatbot/whatsapp/status/` - Connection status

### Hospital Management
- `GET /hospitals/` - List hospitals
- `POST /hospitals/register/` - Register new hospital
- `GET /hospitals/<id>/` - Hospital details

## 🔒 Security Features

- **CSRF Protection**: Comprehensive CSRF token validation
- **Session Security**: Secure session configuration
- **Input Validation**: Custom validators for user input
- **SQL Injection Prevention**: Django ORM protection
- **XSS Protection**: Template auto-escaping
- **Authentication**: Multi-factor authentication support

## 📊 Monitoring & Analytics

### Chat Analytics
- Session tracking and user engagement
- AI performance metrics
- Response time monitoring
- User satisfaction scoring

### System Monitoring
- Error logging and tracking
- Performance metrics
- Database query optimization
- Real-time system health

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up static file serving
- [ ] Configure email backend
- [ ] Set up SSL certificates
- [ ] Configure domain and subdomains
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

### Deployment Options
- **Heroku**: Ready for Heroku deployment
- **Railway**: Railway.app compatible
- **Render**: Render.com ready
- **VPS**: Traditional server deployment
- **Docker**: Containerization ready

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Ensure mobile responsiveness
- Test across different browsers

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp)

### Community
- Create an issue for bug reports


### Professional Support
For enterprise support and custom development:
- Email: symptomwiseprivatelimited@gmail.com | roshanshuklayt@gmail.com   


## 🙏 Acknowledgments

- **BioMistral**: For the medical AI model
- **Django Community**: For the excellent framework
- **Ollama**: For local AI model serving
- **Twilio**: For WhatsApp integration
- **Bootstrap**: For responsive UI components

## 📈 Roadmap

### Upcoming Features
- [ ] Mobile app (React Native)
- [ ] Telemedicine video calls
- [ ] Prescription management
- [ ] Insurance integration
- [ ] Multi-language AI support
- [ ] Advanced analytics dashboard
- [ ] API rate limiting
- [ ] Automated testing suite


---

**Made with ❤️ for better healthcare accessibility**

*This project aims to bridge the gap between patients and healthcare providers through intelligent technology and seamless user experience.*
