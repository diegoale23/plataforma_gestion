# main_project/settings.py
import os
from pathlib import Path

from dotenv import load_dotenv # Añadir import
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-...' # ¡Cambiar en producción!
DEBUG = True # ¡Cambiar a False en producción!

ALLOWED_HOSTS = []

# Cargar variables de entorno desde .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Claves API (¡Guardar de forma segura, no hardcodear!)
INFOJOBS_ACCESS_TOKEN = os.environ.get('INFOJOBS_ACCESS_TOKEN') # Leer desde .env

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Mis aplicaciones
    'users.apps.UsersConfig',
    'projects.apps.ProjectsConfig',
    'market_analysis.apps.MarketAnalysisConfig',
    'ai_engine.apps.AiEngineConfig',

    # Dependencias (ejemplo)
    # 'crispy_forms', # Si usas crispy-forms para mejorar formularios
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # Añade esta línea
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Añade esta línea
    'django.contrib.messages.middleware.MessageMiddleware', # Añade esta línea
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'main_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            os.path.join(BASE_DIR, 'users', 'templates'), # Añade esta línea
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'main_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql', # O 'django.db.backends.mysql'
        'NAME': 'plataforma_db',
        'USER': 'postgres',
        'PASSWORD': 'dacp18419361',
        'HOST': 'localhost', # O la IP/host de tu servidor DB
        'PORT': '5432',      # O el puerto de MySQL (3306)
    }
}

# Password validation
# ... validators por defecto ...

# Internationalization
LANGUAGE_CODE = 'es-es' # Español
TIME_ZONE = 'Europe/Madrid'
USE_I18N = True
USE_L10N = True # Deprecado en Django 5.0, usar USE_I18N
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_collected') # Para producción

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Autenticación
LOGIN_URL = 'login' # Nombre de la URL de inicio de sesión
LOGOUT_REDIRECT_URL = 'home' # A dónde redirigir después de cerrar sesión
LOGIN_REDIRECT_URL = 'dashboard' # A dónde redirigir después de iniciar sesión

# Modelo de usuario personalizado (si es necesario extender el User por defecto)
# AUTH_USER_MODEL = 'users.CustomUser' # Descomentar si creas un modelo de usuario personalizado

# Configuración adicional (ej. email, APIs externas, etc.)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# ... más configuraciones de email ...

# Claves API (¡Guardar de forma segura, no hardcodear!)
INFOJOBS_API_KEY = os.environ.get('INFOJOBS_API_KEY', 'tu_api_key_infojobs')
LINKEDIN_API_KEY = os.environ.get('LINKEDIN_API_KEY', 'tu_api_key_linkedin')
# ... etc ...