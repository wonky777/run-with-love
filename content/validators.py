"""Валидаторы для загружаемых изображений (раздел 19.5 ТЗ — желательное)."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class ImageSizeValidator:
    """Ограничивает максимальный размер загружаемого файла изображения."""

    def __init__(self, max_mb: int | None = None):
        self.max_mb = max_mb or getattr(settings, "MAX_IMAGE_SIZE_MB", 10)

    def __call__(self, file):
        max_bytes = self.max_mb * 1024 * 1024
        if file.size and file.size > max_bytes:
            raise ValidationError(
                f"Файл слишком большой (макс. {self.max_mb} МБ)."
            )

    def __eq__(self, other):
        return isinstance(other, ImageSizeValidator) and self.max_mb == other.max_mb
