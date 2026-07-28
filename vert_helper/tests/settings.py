SECRET_KEY = "vert-helper-tests"
DEBUG = True
USE_TZ = True
TIME_ZONE = "UTC"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "vert_helper",
]

MIDDLEWARE = []
ROOT_URLCONF = "vert_helper.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

VERT_HELPER = {
    "JWT_AUTH_ENABLE": False,
}
