"""
Импорт новостей из JSON ВКонтакте (без токена на сервере).

Администратор сам получает JSON ответа метода wall.get (например, через
VK API Explorer) и вставляет его в админке. Этот модуль разбирает JSON и
создаёт новости, при необходимости скачивая прикреплённые фото на сервер.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone

from django.core.files.base import ContentFile

from ..models import News, NewsImage


class VKJsonError(Exception):
    """Некорректный или нераспознанный JSON."""


def _posts_from_json(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        resp = data.get("response")
        if isinstance(resp, dict) and "items" in resp:
            return resp["items"]
        if isinstance(resp, list):
            return resp
        if "items" in data and isinstance(data["items"], list):
            return data["items"]
        if "id" in data or "text" in data:  # одиночный пост
            return [data]
    raise VKJsonError(
        "Не удалось найти посты. Вставьте ответ метода wall.get "
        "(с ключом response/items) или массив постов."
    )


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
    img.image.save(f"vk_{news.vk_post_id}_{order}.jpg", ContentFile(content), save=True)
    return True


def import_from_json(text: str, download_images: bool = True) -> tuple[int, int]:
    """
    Разбирает JSON и создаёт новости.
    Возвращает (создано_новых, всего_постов_в_JSON).
    """
    text = (text or "").strip()
    if not text:
        raise VKJsonError("Пустой ввод — вставьте JSON.")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise VKJsonError(f"Некорректный JSON: {exc}")

    posts = _posts_from_json(data)
    created = 0
    for post in posts:
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
            "is_visible": True,
        }
        if vk_post_id:
            news, is_new = News.objects.update_or_create(
                vk_post_id=vk_post_id, is_from_vk=True, defaults=defaults
            )
        else:
            news = News.objects.create(is_from_vk=True, **defaults)
            is_new = True

        if is_new:
            created += 1
            if download_images:
                order = 0
                for att in post.get("attachments") or []:
                    if att.get("type") != "photo":
                        continue
                    url = _best_photo_url(att)
                    if url:
                        order += 1
                        _download_image(news, url, order)

    return created, len(posts)
