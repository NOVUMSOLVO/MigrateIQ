"""
Django settings for migrateiq project.
"""

import os
import base64
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-key-for-development-only-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    'django_prometheus',
    'guardian',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'social_django',
    'import_export',
    'actstream',
    # 'notifications',  # Temporarily disabled due to Python 3.13 compatibility
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
    'health_check.contrib.migrations',
    'health_check.contrib.celery',
    'health_check.contrib.redis',
    # Local apps
    'analyzer.apps.AnalyzerConfig',
    'mapping_engine',
    'ml',
    'orchestrator.apps.OrchestratorConfig',
    'transformation',
    'validation',
    'authentication',
    'core',
    'reporting',
    'integrations.apps.IntegrationsConfig',
    'graphql_api.apps.GraphqlApiConfig',
    # NHS Compliance modules
    'nhs_compliance.apps.NhsComplianceConfig',
    'healthcare_standards.apps.HealthcareStandardsConfig',
    # Demo extension
    'demo_extension',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    'core.middleware.RateLimitMiddleware',
    'core.cache_middleware.APIResponseCacheMiddleware',
    'core.cache_middleware.CompressionMiddleware',
    'core.metrics.MetricsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'core.middleware.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.TenantMiddleware',
    'core.middleware.AuditMiddleware',
    'core.cache_middleware.CacheInvalidationMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'migrateiq.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'migrateiq.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en'
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Supported languages
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Español'),
    ('fr', 'Français'),
    ('de', 'Deutsch'),
    ('zh', '中文'),
    ('ja', '日本語'),
    ('ar', 'العربية'),
    ('he', 'עברית'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Allow all origins in development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React frontend
]

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'core.rate_limiting.UserRateThrottle',
        'core.rate_limiting.TenantRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'tenant': '10000/hour'
    }
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Celery settings
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'True') == 'True'
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'migrateiq',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# API Cache Configuration
API_CACHE_TIMEOUT = 300  # 5 minutes default
API_CACHE_HEADERS = True
API_CACHE_CONFIG = {
    '/api/projects/': 600,      # 10 minutes
    '/api/analyzer/': 1800,     # 30 minutes
    '/api/validation/': 300,    # 5 minutes
    '/api/ml/': 3600,          # 1 hour
    '/api/core/': 300,         # 5 minutes
}

# Cache key prefix
CACHE_KEY_PREFIX = 'migrateiq'
CACHE_DEFAULT_TIMEOUT = 300

# Compression settings
COMPRESSION_MIN_LENGTH = 1024  # Only compress responses larger than 1KB

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'migrateiq.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'migrateiq': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'MigrateIQ API',
    'DESCRIPTION': 'AI-powered data migration platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 60

# Static files configuration for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Multi-tenancy settings
TENANT_MODEL = 'core.Tenant'
TENANT_DOMAIN_MODEL = 'core.Domain'

# Custom user model
AUTH_USER_MODEL = 'authentication.User'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.azuread_tenant.AzureADTenantOAuth2',
]

# Site ID for django.contrib.sites
SITE_ID = 1

# Guardian settings for object-level permissions
ANONYMOUS_USER_NAME = None
GUARDIAN_RENDER_403 = True
GUARDIAN_TEMPLATE_403 = '403.html'

# Two-Factor Authentication settings
OTP_TOTP_ISSUER = 'MigrateIQ'
OTP_LOGIN_URL = '/auth/login/'

# Social Authentication settings
SOCIAL_AUTH_POSTGRES_JSONFIELD = True
SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/dashboard/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/auth/login/'

# Google OAuth2 settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('GOOGLE_OAUTH2_SECRET', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

# Microsoft Azure AD settings
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = os.getenv('AZURE_AD_CLIENT_ID', '')
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = os.getenv('AZURE_AD_CLIENT_SECRET', '')
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = os.getenv('AZURE_AD_TENANT_ID', '')

# Activity Stream settings
ACTSTREAM_SETTINGS = {
    'MANAGER': 'actstream.managers.ActionManager',
    'FETCH_RELATIONS': True,
    'USE_PREFETCH': True,
    'USE_JSONFIELD': True,
    'GFK_FETCH_DEPTH': 1,
}

# Notifications settings
DJANGO_NOTIFICATIONS_CONFIG = {
    'USE_JSONFIELD': True,
    'SOFT_DELETE': True,
}

# Import/Export settings
IMPORT_EXPORT_USE_TRANSACTIONS = True
IMPORT_EXPORT_SKIP_ADMIN_LOG = False
IMPORT_EXPORT_TMP_STORAGE_CLASS = 'import_export.tmp_storages.CacheStorage'

# Prometheus metrics settings
PROMETHEUS_EXPORT_MIGRATIONS = False
PROMETHEUS_LATENCY_BUCKETS = (
    0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf')
)

# Rate limiting settings
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Enhanced Rate Limiting Configuration
ENHANCED_RATE_LIMITING = {
    'ENABLE_USER_LIMITS': True,
    'ENABLE_TENANT_LIMITS': True,
    'ENABLE_DYNAMIC_LIMITS': True,
    'ENABLE_ANALYTICS': True,
    'SUBSCRIPTION_TIERS': {
        'free': {
            'user_limit': 100,
            'tenant_limit': 1000,
            'burst_multiplier': 1.5,
        },
        'basic': {
            'user_limit': 500,
            'tenant_limit': 5000,
            'burst_multiplier': 2.0,
        },
        'premium': {
            'user_limit': 2000,
            'tenant_limit': 20000,
            'burst_multiplier': 3.0,
        },
        'enterprise': {
            'user_limit': 10000,
            'tenant_limit': 100000,
            'burst_multiplier': 5.0,
        }
    },
    'ENDPOINT_MULTIPLIERS': {
        '/api/ml/': 0.5,
        '/api/analyzer/': 0.7,
        '/api/orchestrator/': 0.8,
        '/api/validation/': 0.9,
    },
    'MONITORING': {
        'HIGH_UTILIZATION_THRESHOLD': 80,
        'CRITICAL_UTILIZATION_THRESHOLD': 95,
        'ALERT_COOLDOWN': 300,  # 5 minutes
    }
}

# Email settings for notifications
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@migrateiq.com')

# Backup settings
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': os.path.join(BASE_DIR, 'backups')}
DBBACKUP_CLEANUP_KEEP = 10
DBBACKUP_CLEANUP_KEEP_MEDIA = 10

# Feature flags
FEATURE_FLAGS = {
    'ADVANCED_ANALYTICS': os.getenv('FEATURE_ADVANCED_ANALYTICS', 'False') == 'True',
    'ML_RECOMMENDATIONS': os.getenv('FEATURE_ML_RECOMMENDATIONS', 'False') == 'True',
    'REAL_TIME_MONITORING': os.getenv('FEATURE_REAL_TIME_MONITORING', 'False') == 'True',
    'ADVANCED_REPORTING': os.getenv('FEATURE_ADVANCED_REPORTING', 'False') == 'True',
}

# Data quality settings
DATA_QUALITY_CHECKS = {
    'ENABLE_PROFILING': True,
    'ENABLE_VALIDATION': True,
    'ENABLE_MONITORING': True,
    'PROFILE_SAMPLE_SIZE': 10000,
}

# API versioning
REST_FRAMEWORK_VERSION = '1.0'
API_VERSION_HEADER = 'X-API-Version'

# WebSocket settings for real-time features
CHANNELS_REDIS_URL = os.getenv('CHANNELS_REDIS_URL', 'redis://localhost:6379/2')

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:")
CSP_CONNECT_SRC = ("'self'", "wss:", "ws:")

# GDPR Compliance
GDPR_COMPLIANCE = {
    'ENABLE_CONSENT_TRACKING': True,
    'DATA_RETENTION_DAYS': 2555,  # 7 years
    'ENABLE_RIGHT_TO_BE_FORGOTTEN': True,
    'ENABLE_DATA_PORTABILITY': True,
}

# Cloud Integration Settings
CLOUD_INTEGRATIONS = {
    'AWS': {
        'ENABLED': os.getenv('AWS_INTEGRATION_ENABLED', 'True') == 'True',
        'DEFAULT_REGION': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
        'MAX_CONNECTIONS': int(os.getenv('AWS_MAX_CONNECTIONS', '10')),
        'CONNECTION_TIMEOUT': int(os.getenv('AWS_CONNECTION_TIMEOUT', '30')),
    },
    'AZURE': {
        'ENABLED': os.getenv('AZURE_INTEGRATION_ENABLED', 'True') == 'True',
        'DEFAULT_REGION': os.getenv('AZURE_DEFAULT_REGION', 'eastus'),
        'MAX_CONNECTIONS': int(os.getenv('AZURE_MAX_CONNECTIONS', '10')),
        'CONNECTION_TIMEOUT': int(os.getenv('AZURE_CONNECTION_TIMEOUT', '30')),
    },
    'GCP': {
        'ENABLED': os.getenv('GCP_INTEGRATION_ENABLED', 'True') == 'True',
        'DEFAULT_REGION': os.getenv('GCP_DEFAULT_REGION', 'us-central1'),
        'MAX_CONNECTIONS': int(os.getenv('GCP_MAX_CONNECTIONS', '10')),
        'CONNECTION_TIMEOUT': int(os.getenv('GCP_CONNECTION_TIMEOUT', '30')),
    }
}

# PWA Settings
PWA_SETTINGS = {
    'ENABLE_SERVICE_WORKER': os.getenv('PWA_ENABLE_SERVICE_WORKER', 'True') == 'True',
    'ENABLE_PUSH_NOTIFICATIONS': os.getenv('PWA_ENABLE_PUSH_NOTIFICATIONS', 'True') == 'True',
    'VAPID_PUBLIC_KEY': os.getenv('VAPID_PUBLIC_KEY', ''),
    'VAPID_PRIVATE_KEY': os.getenv('VAPID_PRIVATE_KEY', ''),
    'CACHE_STRATEGY': os.getenv('PWA_CACHE_STRATEGY', 'cache_first'),
    'OFFLINE_FALLBACK': os.getenv('PWA_OFFLINE_FALLBACK', '/offline.html'),
}

# Advanced ML Settings
ML_SETTINGS = {
    'ENABLE_ADVANCED_MODELS': os.getenv('ML_ENABLE_ADVANCED_MODELS', 'True') == 'True',
    'MODEL_CACHE_TIMEOUT': int(os.getenv('ML_MODEL_CACHE_TIMEOUT', '3600')),
    'MAX_TRAINING_SAMPLES': int(os.getenv('ML_MAX_TRAINING_SAMPLES', '100000')),
    'PROFILING_SAMPLE_SIZE': int(os.getenv('ML_PROFILING_SAMPLE_SIZE', '10000')),
    'QUALITY_ASSESSMENT_THRESHOLD': float(os.getenv('ML_QUALITY_THRESHOLD', '0.8')),
}

# Audit settings
AUDIT_LOG_RETENTION_DAYS = 2555  # 7 years for compliance
AUDIT_SENSITIVE_FIELDS = ['password', 'token', 'secret', 'key']

# Performance monitoring
PERFORMANCE_MONITORING = {
    'ENABLE_QUERY_MONITORING': True,
    'SLOW_QUERY_THRESHOLD': 1.0,  # seconds
    'ENABLE_MEMORY_MONITORING': True,
    'ENABLE_CPU_MONITORING': True,
}

# Metrics configuration
METRICS_ENABLED = True
METRICS_COLLECT_INTERVAL = 60  # seconds

# API versioning
API_SUPPORTED_VERSIONS = ['1.0', '1.1', '2.0']
API_DEPRECATED_VERSIONS = ['1.0']
API_SUNSET_VERSIONS = {
    '1.0': '2024-12-31'
}

API_VERSIONS = {
    '1.0': {
        'status': 'deprecated',
        'sunset_date': '2024-12-31',
        'description': 'Initial API version'
    },
    '1.1': {
        'status': 'stable',
        'description': 'Enhanced API with additional features'
    },
    '2.0': {
        'status': 'beta',
        'description': 'Major API redesign'
    }
}

# GraphQL Settings
GRAPHENE = {
    'SCHEMA': 'graphql_api.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

# NHS Compliance Settings
NHS_COMPLIANCE = {
    'DSPT_MONITORING_ENABLED': True,
    'CQC_AUDIT_RETENTION_YEARS': 7,
    'PATIENT_SAFETY_REPORTING_ENABLED': True,
    'AUTOMATIC_INCIDENT_DETECTION': True,
}

# NHS Encryption Settings (DSPT Requirements)
NHS_ENCRYPTION_MASTER_KEY = os.getenv('NHS_ENCRYPTION_MASTER_KEY', base64.b64encode(secrets.token_bytes(32)).decode())
NHS_ENCRYPTION_KEY_ROTATION_DAYS = int(os.getenv('NHS_ENCRYPTION_KEY_ROTATION_DAYS', '90'))
NHS_BACKUP_ROOT = os.getenv('NHS_BACKUP_ROOT', '/var/backups/migrateiq')

# Healthcare Standards Settings
HEALTHCARE_STANDARDS_ENABLED = True
HEALTHCARE_STANDARDS = {
    'HL7_VALIDATION_ENABLED': True,
    'FHIR_VALIDATION_ENABLED': True,
    'DICOM_VALIDATION_ENABLED': True,
    'NHS_NUMBER_VALIDATION_ENABLED': True,
    'SNOMED_CT_VALIDATION_ENABLED': False,  # Requires license
    'ICD_10_VALIDATION_ENABLED': False,     # Requires license
}

# DSPT (Data Security and Protection Toolkit) Settings
DSPT_SETTINGS = {
    'ENCRYPTION_AT_REST': 'AES-256',
    'ENCRYPTION_IN_TRANSIT': 'TLS-1.3',
    'ACCESS_CONTROL_REQUIRED': True,
    'MFA_REQUIRED': True,
    'AUDIT_RETENTION_YEARS': 7,
    'BACKUP_FREQUENCY_HOURS': 24,
    'RECOVERY_TIME_OBJECTIVE_HOURS': 4,
    'RECOVERY_POINT_OBJECTIVE_HOURS': 1,
}

# CQC (Care Quality Commission) Settings
CQC_SETTINGS = {
    'AUDIT_TRAIL_ENABLED': True,
    'PATIENT_SAFETY_MONITORING': True,
    'INCIDENT_REPORTING_ENABLED': True,
    'COMPLIANCE_DASHBOARD_ENABLED': True,
    'AUTOMATIC_ALERTS_ENABLED': True,
}

# GraphQL JWT Settings
GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=60),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
}
