"""Корневые URL проекта."""

from pathlib import Path

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = "Run With Love — администрирование"
admin.site.site_title = "Run With Love"
admin.site.index_title = "Управление контентом сайта"


def spa_serve(request, path=""):
    """
    Отдаёт собранный React-сайт (режим «всё в одном»).
    Файлы (assets, иконки) отдаются как есть; на остальные пути — index.html.
    """
    dist = Path(settings.FRONTEND_DIST)
    index = dist / "index.html"
    if not index.exists():
        raise Http404(
            "Фронт не собран. Выполните `npm run build` и положите dist в static_site/."
        )
    if path:
        candidate = dist / path
        if candidate.is_file():
            return serve(request, path, document_root=str(dist))
    return FileResponse(open(index, "rb"))


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("content.urls")),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
]

# Медиа-файлы (загруженные через админку).
# ВАЖНО: helper static() работает только при DEBUG=True, поэтому в продакшене
# (DEBUG=False) загруженные фото не отдавались бы и показывались «битыми».
# Отдаём media через явный маршрут всегда — это корректно для небольшого
# контент-сайта на одном сервере (раздел 11 ТЗ).
media_url = settings.MEDIA_URL.lstrip("/")
urlpatterns += [
    re_path(
        rf"^{media_url}(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]

# Собранный фронт на остальных путях (catch-all — обязательно последним).
urlpatterns += [re_path(r"^(?P<path>.*)$", spa_serve)]
