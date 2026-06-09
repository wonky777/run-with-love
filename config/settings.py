"""
Django settings for the Run With Love backend.

Простой single-app проект: контент-CMS для уже готового React-сайта.
Конфигурация читается из переменных окружения (.env), значения по умолчанию
подходят для локальной разработки.
"""

from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем .env из корня backend/, если он есть.
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0").strip() in {"1", "true", "True", "yes"}


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --- Базовые настройки ---
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")
# В режиме разработки разрешаем любой хост — чтобы работали публичные туннели
# (ngrok / cloudflared / localtunnel) для отправки ссылки «на согласование».
if DEBUG:
    ALLOWED_HOSTS = ["*"]
# Доверенные origin для CSRF (нужно для входа в админку через https-туннель).
# Пример: CSRF_TRUSTED_ORIGINS=https://your-tunnel.trycloudflare.com
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")

# --- Приложения ---
INSTALLED_APPS = [
    "jazzmin",  # современная тема админки (должна быть ПЕРЕД django.contrib.admin)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Сторонние
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "adminsortable2",      # drag-and-drop сортировка
    "django_ckeditor_5",   # редактор текста
    "drf_spectacular",     # OpenAPI/Swagger документация
    # Наше приложение
    "content",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- База данных: SQLite (раздел 3 ТЗ) ---
# Путь к SQLite можно переопределить через SQLITE_PATH — чтобы положить базу
# на постоянный Volume (например, на Railway), иначе данные теряются при редеплое.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
    }
}

# --- Пароли ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Локализация ---
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# --- Статика и медиа ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
# Путь к загруженным файлам можно переопределить через MEDIA_ROOT — чтобы
# положить media на постоянный Volume (например, на Railway), иначе загруженные
# фото пропадают при каждом редеплое.
MEDIA_ROOT = os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Хранилище статики: whitenoise отдаёт CSS/JS админки и DRF на проде (Railway и т.п.).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# --- Django REST Framework: публичное read-only API без авторизации ---
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Авторизация по токену (для записи) + сессия (для браузерного API/админки).
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# --- CORS: разрешаем фронту (Vite) обращаться к API ---
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
# В режиме разработки можно разрешить все источники.
CORS_ALLOW_ALL_ORIGINS = DEBUG

# --- Ограничения на загружаемые изображения (раздел 19.5 ТЗ, желательное) ---
# Максимальный размер файла изображения в мегабайтах.
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp", "gif"]

# --- Автоимпорт новостей из ВКонтакте (раздел 19.1 ТЗ, желательное) ---
# Токен доступа VK API (сервисный ключ сообщества или пользователя).
# Без токена автоимпорт не работает, ручное создание новостей — работает всегда.
VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN", "")
# Короткое имя сообщества: vk.com/<domain>.
VK_GROUP_DOMAIN = os.getenv("VK_GROUP_DOMAIN", "runwithlove")

# --- Собранный фронт (режим «всё в одном»): Django отдаёт React-сайт ---
# Папка с результатом `npm run build` (vite). Если её нет — работает только API/админка.
FRONTEND_DIST = BASE_DIR / "static_site"


# --- Тема админки (Jazzmin) ---
JAZZMIN_SETTINGS = {
    "site_title": "Run With Love",
    "site_header": "Run With Love",
    "site_brand": "Run With Love",
    "welcome_sign": "Панель управления сайтом Run With Love",
    "copyright": "Run With Love",
    "search_model": ["content.Race", "content.News"],
    "show_ui_builder": False,
    # Подсказка-приветствие в боковом меню для не-технического администратора.
    "site_logo_classes": "img-circle",
    # Понятный порядок разделов: сначала контент сайта, технические — в конце.
    "order_with_respect_to": [
        "content",
        "content.Race",
        "content.RaceDistance",
        "content.News",
        "content.Gallery",
        "content.Partner",
        "content.Beneficiary",
        "content.Report",
        "content.TeamMember",
        "content.Achievement",
        "content.OrganizationInfo",
        "auth",
    ],
    # Скрываем технические модели, которые администратору-контентщику не нужны:
    # отдельные «Изображения» (они редактируются прямо внутри новости/альбома)
    # и токены DRF.
    "hide_models": [
        "content.NewsImage",
        "content.GalleryImage",
        "content.RaceDistance",
        "authtoken.TokenProxy",
    ],
    "icons": {
        "auth": "fas fa-lock",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "content.Race": "fas fa-person-running",
        "content.RaceDistance": "fas fa-ruler-horizontal",
        "content.News": "fas fa-newspaper",
        "content.NewsImage": "fas fa-image",
        "content.Partner": "fas fa-handshake",
        "content.Beneficiary": "fas fa-hand-holding-heart",
        "content.Gallery": "fas fa-images",
        "content.GalleryImage": "fas fa-image",
        "content.TeamMember": "fas fa-people-group",
        "content.Achievement": "fas fa-trophy",
        "content.Report": "fas fa-file-lines",
        "content.OrganizationInfo": "fas fa-circle-info",
    },
    # Одна простая ссылка в верхнем меню — открыть сайт. Без лишнего.
    "topmenu_links": [
        {"name": "Открыть сайт", "url": "/", "new_window": True},
    ],
    # Меню раскрыто; связанные объекты — во всплывающем окне.
    "related_modal_active": True,
    "navigation_expanded": True,
    # Формы — единой простой страницей (всё видно сразу, без вкладок и аккордеонов).
    "changeform_format": "single",
}
# Минималистичная светлая тема: светлый сайдбар, белая шапка, плоский стиль,
# без ярких акцентов и крупных цветных кнопок.
JAZZMIN_UI_TWEAKS = {
    "theme": "default",
    "dark_mode_theme": None,
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-light-primary",
    "sidebar_nav_flat_style": True,
    "accent": "accent-primary",
    "brand_colour": False,
    "navbar_small_text": False,
    "body_small_text": False,
    "sidebar_nav_small_text": False,
    "actions_sticky_top": True,
}

# --- Редактор текста (CKEditor 5) ---
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading", "|",
            "bold", "italic", "link",
            "bulletedList", "numberedList", "blockQuote", "|",
            "undo", "redo",
        ],
    },
}


# --- Документация API (drf-spectacular) ---
SPECTACULAR_SETTINGS = {
    "TITLE": "Run With Love API",
    "DESCRIPTION": "Публичное read-only API сайта благотворительных забегов.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
