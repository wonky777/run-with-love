"""
Автоматический импорт новостей из сообщества ВКонтакте через VK API
(раздел 19.1 ТЗ).

В отличие от ручного создания новостей в админке (которое остаётся основным
способом), этот модуль сам ходит в VK API методом wall.get, получает последние
посты сообщества https://vk.com/runwithlove и сохраняет их в модель News.

Хранятся только последние N (по умолчанию 10) импортированных VK-новостей —
старые автоимпортированные записи удаляются (раздел 19.1 ТЗ).

Требуется access-токен VK в переменной окружения VK_ACCESS_TOKEN
(сервисный ключ доступа сообщества или пользователя). Без токена автоимпорт
не выполняется, а ручное создание новостей продолжает работать.
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from django.conf import settings
from django.core.files.base import ContentFile

from ..models import News, NewsImage

VK_API_VERSION = "5.199"
VK_WALL_GET_URL = "https://api.vk.com/method/wall.get"

# Сколько последних VK-новостей храним (раздел 19.1 ТЗ).
VK_KEEP_LAST = 10


class VKApiError(Exception):
    """Ошибка обращения к VK API или конфигурации."""


def _get_token() -> str:
    token = getattr(settings, "VK_ACCESS_TOKEN", "") or os.getenv("VK_ACCESS_TOKEN", "")
    if not token:
        raise VKApiError(
            "Не задан токен VK. Укажите VK_ACCESS_TOKEN в .env, чтобы включить "
            "автоимпорт новостей из ВКонтакте."
        )
    return token


def _get_domain() -> str:
    # Короткое имя сообщества (vk.com/<domain>).
    return getattr(settings, "VK_GROUP_DOMAIN", "") or os.getenv(
        "VK_GROUP_DOMAIN", "runwithlove"
    )


def _call_wall_get(count: int) -> list[dict]:
    params = {
        "domain": _get_domain(),
        "count": count,
        "access_token": _get_token(),
        "v": VK_API_VERSION,
    }
    url = f"{VK_WALL_GET_URL}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # сеть/JSON
        raise VKApiError(f"Не удалось получить данные из VK API: {exc}")

    if "error" in payload:
        err = payload["error"]
        msg = err.get("error_msg", "неизвестная ошибка")
        raise VKApiError(f"VK API вернул ошибку: {msg}")

    response = payload.get("response") or {}
    return response.get("items", []) or []


def _best_photo_url(attachment: dict):
    photo = attachment.get("photo") or {}
    sizes = photo.get("sizes") or []
    if sizes:
        best = max(sizes, key=lambda s: s.get("width", 0) * s.get("height", 0))
        return best.get("url")
    for key in ("photo_2560", "photo_1280", "photo_807", "photo_604"):
        if photo.get(key):
            return photo[key]
    return None


def _download_image(news: News, url: str, order: int) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
    except Exception:
        return False
    img = NewsImage(news=news, sort_order=order)
    img.image.save(
        f"vk_{news.vk_post_id or news.pk}_{order}.jpg", ContentFile(content), save=True
    )
    return True


def _prune_old_vk_news(keep: int = VK_KEEP_LAST) -> int:
    """Оставляет только последние `keep` автоимпортированных VK-новостей."""
    extra_ids = list(
        News.objects.filter(is_from_vk=True)
        .order_by("-date", "-created_at")
        .values_list("id", flat=True)[keep:]
    )
    if not extra_ids:
        return 0
    deleted, _ = News.objects.filter(id__in=extra_ids).delete()
    return len(extra_ids)


def _upsert_post(post: dict, download_images: bool = True) -> str:
    """Создаёт или обновляет одну новость из поста VK. Возвращает 'created'/'updated'."""
    owner_id = post.get("owner_id", "")
    post_id = post.get("id", "")
    vk_post_id = f"{owner_id}_{post_id}" if post_id != "" else ""
    published = post.get("date")
    post_date = (
        datetime.fromtimestamp(published, tz=timezone.utc).date()
        if published
        else datetime.now(tz=timezone.utc).date()
    )
    post_url = f"https://vk.com/wall{vk_post_id}" if vk_post_id else ""

    defaults = {
        "text": (post.get("text") or "").strip(),
        "date": post_date,
        "source_url": post_url,
    }

    if vk_post_id:
        news, is_new = News.objects.get_or_create(
            vk_post_id=vk_post_id,
            is_from_vk=True,
            defaults={**defaults, "is_visible": True},
        )
        if not is_new:
            # Обновляем текст/дату/ссылку, не трогая is_visible (могли скрыть руками).
            for field, value in defaults.items():
                setattr(news, field, value)
            news.save(update_fields=list(defaults.keys()) + ["updated_at"])
            return "updated"
    else:
        news = News.objects.create(is_from_vk=True, is_visible=True, **defaults)

    if download_images:
        order = 0
        for att in post.get("attachments") or []:
            if att.get("type") != "photo":
                continue
            url = _best_photo_url(att)
            if url:
                order += 1
                _download_image(news, url, order)
    return "created"


def import_latest_from_vk(count: int = VK_KEEP_LAST, download_images: bool = True) -> dict:
    """
    Импортирует последние посты сообщества VK в News.

    Возвращает словарь со статистикой:
    {"fetched": int, "created": int, "updated": int, "pruned": int}.
    """
    items = _call_wall_get(count)
    created = 0
    updated = 0
    for post in items:
        if _upsert_post(post, download_images) == "created":
            created += 1
        else:
            updated += 1

    pruned = _prune_old_vk_news()
    return {
        "fetched": len(items),
        "created": created,
        "updated": updated,
        "pruned": pruned,
    }


def _parse_post_url(url: str) -> str:
    """
    Извлекает идентификатор поста VK из ссылки.
    Поддерживает: vk.com/wall-123_456, vk.com/runwithlove?w=wall-123_456 и т.п.
    Возвращает строку вида "-123_456".
    """
    if not url:
        raise VKApiError("Пустая ссылка на пост.")
    m = re.search(r"wall(-?\d+_\d+)", url)
    if not m:
        raise VKApiError(
            "Не удалось распознать ссылку на пост. Пример правильной ссылки: "
            "https://vk.com/wall-123456_789"
        )
    return m.group(1)


def _call_wall_get_by_id(post_id: str) -> dict:
    """Получает один пост через VK API wall.getById."""
    params = {
        "posts": post_id,
        "access_token": _get_token(),
        "v": VK_API_VERSION,
    }
    url = f"https://api.vk.com/method/wall.getById?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise VKApiError(f"Не удалось получить пост из VK API: {exc}")

    if "error" in payload:
        raise VKApiError(
            f"VK API вернул ошибку: {payload['error'].get('error_msg', 'неизвестно')}"
        )

    response = payload.get("response")
    # Новый формат: {"items": [...]}; старый: [...] .
    items = response.get("items") if isinstance(response, dict) else response
    if not items:
        raise VKApiError("Пост не найден или недоступен.")
    return items[0]


def import_single_post_by_url(url: str, download_images: bool = True) -> dict:
    """
    Импортирует один пост ВКонтакте по ссылке.
    Возвращает {"result": "created"|"updated"}.
    """
    post_id = _parse_post_url(url)
    post = _call_wall_get_by_id(post_id)
    result = _upsert_post(post, download_images)
    return {"result": result}
