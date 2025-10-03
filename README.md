# Data Analysis AI Web Application

A production-ready, AI-powered data analysis web application built with Django that provides intelligent insights, dynamic chart generation, and secure file processing capabilities.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2.7-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5--turbo-purple.svg)


## Technology Stack

### **Backend Framework**
- **Django 4.2.7**: Robust web framework with built-in security
- **Python 3.11+**: Modern Python with type hints and async support
- **PostgreSQL**: Production-ready relational database
- **SQLite**: Development database for local testing

### **AI & Data Processing**
- **OpenAI GPT-3.5-turbo**: Advanced language model for data analysis
- **Pandas**: Powerful data manipulation and analysis
- **Matplotlib**: Professional chart generation and visualization
- **NumPy**: Numerical computing and array operations

### **Frontend Technologies**
- **HTML5**: Semantic markup and modern web standards
- **CSS3**: Responsive design with Flexbox and Grid
- **JavaScript (ES6+)**: AJAX, DOM manipulation, and dynamic updates
- **Bootstrap**: Responsive CSS framework (optional enhancement)

## Prerequisites

- **Python 3.11+**
- **OpenAI API Key**
- **Git**

## Quick Start

### 1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/data-analysis-ai.git
cd data-analysis-ai
```

### 2. **Set Up Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4. **Configure Environment Variables**
```bash
cp env.example .env
# Edit .env with your actual values
```

### 5. **Run Database Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. **Create Superuser (Optional)**
```bash
python manage.py createsuperuser
```

### 7. **Start Development Server**
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see your application!

## Configuration

### **Environment Variables**

Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# OpenAI API
OPENAI_API_KEY=your-openai-api-key-here

# Database (for production)
# DATABASE_URL=postgres://username:password@host:port/database
```

### **File Upload Requirements**

Your application enforces strict file validation:

- **File Type**: Only `.csv` files accepted
- **File Size**: Maximum 10MB per file
- **Content**: Must contain actual data (not empty)
- **Rows**: Maximum 100,000 rows
- **Columns**: Maximum 100 columns
- **Data Types**: Must contain numeric columns for analysis
- **Encoding**: UTF-8 encoding required

## Structure

```
dataai/
├── analysis/                 # Main analysis app
│   ├── models.py            # Data models (DataSet, Chat, ChatMessage)
│   ├── views.py             # Business logic and file processing
│   ├── utils.py             # AI integration and chart generation
│   └── forms.py             # Form definitions
├── users/                   # User authentication app
│   ├── models.py            # Custom user model
│   ├── views.py             # Authentication views
│   └── forms.py             # User registration forms
├── backend/                 # Project configuration
│   ├── settings.py          # Django settings (dev/prod)
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py              # WSGI application entry point
├── templates/               # HTML templates
│   ├── analysis/            # Analysis page templates
│   ├── users/               # Authentication templates
│   └── base.html            # Base template
├── static/                  # Static files (CSS, JS, images)
├── media/                   # User uploaded files
├── requirements.txt         # Python dependencies
├── Procfile                 # Heroku deployment configuration
├── runtime.txt              # Python version specification
└── manage.py                # Django management script
```

## 🔒 Security 

### **File Upload Security**
- **Type Validation**: Strict CSV file type checking
- **Size Limits**: Configurable file size restrictions
- **Content Validation**: Ensures uploaded files contain valid data
- **Malware Protection**: File content analysis and validation

### **Application Security**
- **HTTPS Enforcement**: Automatic SSL redirect in production
- **Security Headers**: Comprehensive security header configuration
- **CSRF Protection**: Built-in CSRF token validation
- **Session Security**: Secure session configuration
- **Input Validation**: Comprehensive input sanitization

### **Data Protection**
- **User Isolation**: Users can only access their own data
- **Secure Storage**: Encrypted file storage and database
- **Audit Logging**: Comprehensive logging for security monitoring

## 📊 Performance 

### **Static File Optimization**
- **Whitenoise**: Efficient static file serving
- **Compression**: Automatic file compression
- **Caching**: Intelligent caching strategies
- **CDN Ready**: Easy integration with CDN services

### **Database Optimization**
- **Connection Pooling**: Optimized database connections
- **Query Optimization**: Efficient database queries
- **Indexing**: Strategic database indexing
- **Migration Management**: Smooth database schema updates

## 🚀 API 

### **OpenAI Integration**
- **GPT-3.5-turbo**: Advanced language model for analysis
- **Rate Limiting**: Built-in API rate limiting
- **Error Handling**: Comprehensive error handling and fallbacks
- **Timeout Management**: Configurable API timeouts

### **Chart Generation API**
- **Dynamic Charts**: Automatic chart type selection
- **Multiple Formats**: Support for various chart types
- **Customization**: Configurable chart parameters
- **Export Options**: Chart export capabilities

If you would like to contribute!
1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### **Development Guidelines**
- Follow PEP 8 Python style guidelines
- Write comprehensive tests for new features
- Update documentation for any changes
- Ensure all tests pass before submitting

### **Version 2.0 (Planned)**
- [ ] Real-time chat updates with WebSockets
- [ ] Advanced chart customization options
- [ ] Data export functionality (Excel, PDF)
- [ ] Team collaboration features
- [ ] API endpoints for external integrations

### **Version 3.0 (Future)**
- [ ] Machine learning model integration
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Mobile app development
- [ ] Enterprise features and SSO

