# Data Analysis AI Web Application

A production-ready, AI-powered data analysis web application built with Django that provides intelligent insights, dynamic chart generation, and secure file processing capabilities.

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

