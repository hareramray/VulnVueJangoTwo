"""
Django settings for vulnproject.

============================================================================
  !!  DELIBERATELY INSECURE TRAINING APP  !!
  Every weakness in this file is intentional and labelled [VULN-11-...].
  See docs/Break_and_Fix_Guide.pdf for how to exploit and remediate each one.
  DO NOT deploy this anywhere reachable from the internet.
============================================================================
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# [VULN-11-CONFIG] Hard-coded, guessable secret key committed to source.
#   Fix: load from environment / secrets manager, rotate, keep out of VCS.
SECRET_KEY = "django-insecure-trainingkey-123456"

# [VULN-11-CONFIG] DEBUG on in a "shipped" app leaks stack traces, settings,
#   SQL and local variables on any error page.
#   Fix: DEBUG = False in production and configure proper error pages.
DEBUG = True

# [VULN-11-CONFIG] Wildcard host header allows Host-header poisoning.
#   Fix: pin ALLOWED_HOSTS to the real domain(s).
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "vulnapp",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # [VULN-06-CSRF] CsrfViewMiddleware is intentionally DISABLED so forged
    #   cross-site POSTs are accepted. Fix: re-enable the line below.
    # "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # [VULN-11-CONFIG] Permissive CORS that reflects any Origin and allows
    #   credentials -> any website can call the API as the logged-in user.
    #   Fix: restrict to a known allow-list and never pair "*" with creds.
    "vulnapp.middleware.WideOpenCorsMiddleware",
]

ROOT_URLCONF = "vulnproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "vulnproject.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# [VULN-01-AUTH] Password validators removed, so "123456" is accepted.
#   Fix: restore AUTH_PASSWORD_VALIDATORS (length, common-password, etc.).
AUTH_PASSWORD_VALIDATORS = []

# [VULN-01-AUTH] MD5 hasher makes stored passwords trivially crackable.
#   Fix: keep Django's default (Argon2/PBKDF2) hashers, drop MD5.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# [VULN-03-SESSION] Session cookie hardening turned off and a very long,
#   non-expiring-on-browser-close lifetime. Fix: set Secure, HttpOnly stays
#   on, SameSite=Lax/Strict, and a sane age + expire-at-browser-close.
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# [VULN-11-CONFIG] Security headers left at insecure defaults.
#   Fix: SECURE_SSL_REDIRECT, SECURE_HSTS_SECONDS, X_FRAME_OPTIONS="DENY",
#   SECURE_CONTENT_TYPE_NOSNIFF=True, a Content-Security-Policy, etc.
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
X_FRAME_OPTIONS = "ALLOWALL"
SECURE_CONTENT_TYPE_NOSNIFF = False
CSRF_COOKIE_SECURE = False
