"""
Модели контента для сайта благотворительных забегов «Run With Love».

Все публичные сущности имеют признак is_visible: скрытие записи с сайта
выполняется через is_visible=False (раздел 6 ТЗ), физическое удаление не
является основным сценарием.

Желательные поля (разделы 19.2, 19.3, 19.7 ТЗ) — SEO, координаты, sort_order —
добавлены, но все опциональны и не мешают базовой работе.
"""

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify

from .validators import ImageSizeValidator

# Общий набор валидаторов для всех картинок: тип файла + размер.
IMAGE_VALIDATORS = [
    FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp", "gif"]),
    ImageSizeValidator(),
]


class SeoFieldsMixin(models.Model):
    """SEO-поля (раздел 19.2 ТЗ — желательное). Все опциональны."""

    seo_title = models.CharField(
        "SEO-заголовок", max_length=255, blank=True
    )
    seo_description = models.TextField("SEO-описание", blank=True)
    og_image = models.ImageField(
        "OG-изображение",
        upload_to="seo/",
        null=True,
        blank=True,
        validators=IMAGE_VALIDATORS,
    )

    class Meta:
        abstract = True


class Partner(SeoFieldsMixin):
    """Партнёр или инфопартнёр проекта (раздел 7.6 ТЗ)."""

    name = models.CharField("Название", max_length=255)
    slug = models.SlugField("Slug (ЧПУ)", max_length=255, unique=True, blank=True)
    description = models.TextField("Описание", blank=True)
    logo = models.ImageField(
        "Логотип",
        upload_to="partners/",
        null=True,
        blank=True,
        validators=IMAGE_VALIDATORS,
    )
    website_url = models.URLField("Сайт партнёра", blank=True)
    sort_order = models.IntegerField("Порядок сортировки", default=0)
    is_visible = models.BooleanField("Отображать на сайте", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Партнёр"
        verbose_name_plural = "Партнёры"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Partner, self.name)
        super().save(*args, **kwargs)


class Beneficiary(SeoFieldsMixin):
    """
    Благополучатель — фонд или организация, которым помогает проект (раздел 7.5).

    ВНИМАНИЕ (раздел 10.4 ТЗ): запрещено добавлять поля для прямых платежей
    и реквизитов. Допустима только ссылка на официальный внешний сайт фонда.
    """

    name = models.CharField("Название", max_length=255)
    slug = models.SlugField("Slug (ЧПУ)", max_length=255, unique=True, blank=True)
    description = models.TextField("Описание", blank=True)
    logo_or_photo = models.ImageField(
        "Логотип или фото",
        upload_to="beneficiaries/",
        null=True,
        blank=True,
        validators=IMAGE_VALIDATORS,
    )
    website_url = models.URLField("Официальный сайт", blank=True)
    sort_order = models.IntegerField("Порядок сортировки", default=0)
    is_visible = models.BooleanField("Отображать на сайте", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Благополучатель"
        verbose_name_plural = "Благополучатели"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Beneficiary, self.name)
        super().save(*args, **kwargs)


class Race(SeoFieldsMixin):
    """Отдельный забег (раздел 7.1 ТЗ). Забег всегда длится один день."""

    STATUS_UPCOMING = "upcoming"
    STATUS_REGISTRATION_OPEN = "registration_open"
    STATUS_REGISTRATION_CLOSED = "registration_closed"
    STATUS_FINISHED = "finished"

    STATUS_CHOICES = [
        (STATUS_UPCOMING, "Скоро"),
        (STATUS_REGISTRATION_OPEN, "Идёт регистрация"),
        (STATUS_REGISTRATION_CLOSED, "Регистрация закрыта"),
        (STATUS_FINISHED, "Прошёл"),
    ]

    title = models.CharField("Название", max_length=255)
    slug = models.SlugField("Slug (ЧПУ)", max_length=255, unique=True, blank=True)
    date = models.DateField("Дата проведения")
    status = models.CharField(
        "Статус", max_length=32, choices=STATUS_CHOICES, default=STATUS_UPCOMING
    )
    short_description = models.TextField("Краткое описание", blank=True)
    description = models.TextField("Полное описание", blank=True)
    location_text = models.CharField("Место проведения", max_length=255, blank=True)
    cover_image = models.ImageField(
        "Обложка",
        upload_to="races/",
        null=True,
        blank=True,
        validators=IMAGE_VALIDATORS,
    )

    # Внешние ссылки. Прямые пожертвования и платёжные ссылки запрещены (раздел 7.1).
    russian_running_url = models.URLField("Ссылка на регистрацию", blank=True)
    results_url = models.URLField("Ссылка на результаты", blank=True)
    rules_url = models.URLField("Ссылка на правила", blank=True)
    route_url = models.URLField("Ссылка на маршрут", blank=True)
    external_info_url = models.URLField("Доп. внешняя ссылка", blank=True)

    # Координаты для карты (раздел 19.3 ТЗ — желательное).
    latitude = models.DecimalField(
        "Широта", max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        "Долгота", max_digits=9, decimal_places=6, null=True, blank=True
    )

    # Связи (раздел 8 ТЗ).
    partners = models.ManyToManyField(
        Partner, blank=True, related_name="races", verbose_name="Партнёры"
    )
    beneficiaries = models.ManyToManyField(
        Beneficiary, blank=True, related_name="races", verbose_name="Благополучатели"
    )

    sort_order = models.IntegerField("Порядок сортировки", default=0)
    is_visible = models.BooleanField("Отображать на сайте", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Забег"
        verbose_name_plural = "Забеги"
        ordering = ["sort_order", "-date"]

    def __str__(self) -> str:
        return f"{self.title} ({self.date})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Race, self.title)
        super().save(*args, **kwargs)


class RaceDistance(models.Model):
    """Дистанция внутри забега (раздел 7.2 ТЗ). У забега их может быть несколько."""

    race = models.ForeignKey(
        Race,
        related_name="distances",
        on_delete=models.CASCADE,
        verbose_name="Забег",
    )
    length = models.CharField("Дистанция", max_length=100, help_text='Например: "5 км"')
    age_category = models.CharField(
        "Возрастная категория",
        max_length=100,
        blank=True,
        help_text='Например: "18+" или "детский забег"',
    )
    sort_order = models.IntegerField("Порядок сортировки", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Дистанция забега"
        verbose_name_plural = "Дистанции забегов"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        parts = [self.length]
        if self.age_category:
            parts.append(self.age_category)
        return " · ".join(parts)


class News(SeoFieldsMixin):
    """Новость на сайте (раздел 7.3 ТЗ). Заголовок может быть пустым (пост-формат)."""

    title = models.CharField("Заголовок", max_length=255, blank=True)
    slug = models.SlugField("Slug (ЧПУ)", max_length=255, unique=True, blank=True)
    text = models.TextField("Текст")
    date = models.DateField("Дата")
    source_url = models.URLField("Внешняя ссылка", blank=True)

    # Поля для VK-интеграции (раздел 19.1 ТЗ).
    is_from_vk = models.BooleanField("Импортировано из VK", default=False)
    vk_post_id = models.CharField("ID поста VK", max_length=100, blank=True)

    sort_order = models.IntegerField("Порядок сортировки", default=0)
    is_visible = models.BooleanField("Отображать на сайте", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ["sort_order", "-date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["vk_post_id"],
                condition=models.Q(is_from_vk=True),
                name="unique_vk_post_id",
            )
        ]

    def __str__(self) -> str:
        return self.title or f"Новость от {self.date}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = self.title or f"news-{self.date}"
            self.slug = _unique_slug(News, base)
        super().save(*args, **kwargs)


class NewsImage(models.Model):
    """Изображение в галерее новости (раздел 7.4 ТЗ)."""

    news = models.ForeignKey(
        News,
        related_name="images",
        on_delete=models.CASCADE,
        verbose_name="Новость",
    )
    image = models.ImageField(
        "Изображение", upload_to="news/", validators=IMAGE_VALIDATORS
    )
    sort_order = models.IntegerField("Порядок сортировки", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Изображение новости"
        verbose_name_plural = "Изображения новостей"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"Изображение #{self.pk} для новости «{self.news}»"


class Gallery(SeoFieldsMixin):
    """Фотоальбом / фотоотчёт (раздел 7.7 ТЗ). Может быть без привязки к забегу."""

    title = models.CharField("Название", max_length=255)
    slug = models.SlugField("Slug (ЧПУ)", max_length=255, unique=True, blank=True)
    description = models.TextField("Описание", blank=True)
    race = models.ForeignKey(
        Race,
        related_name="galleries",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Забег",
    )
    date = models.DateField("Дата", null=True, blank=True)
    sort_order = models.IntegerField("Порядок сортировки", default=0)
    is_visible = models.BooleanField("Отображать на сайте", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Фотоальбом"
        verbose_name_plural = "Фотоальбомы"
        ordering = ["sort_order", "-date", "-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Gallery, self.title)
        super().save(*args, **kwargs)


class GalleryImage(models.Model):
    """Изображение фотоальбома (раздел 7.8 ТЗ)."""

    gallery = models.ForeignKey(
        Gallery,
        related_name="images",
        on_delete=models.CASCADE,
        verbose_name="Фотоальбом",
    )
    image = models.ImageField(
        "Изображение", upload_to="galleries/", validators=IMAGE_VALIDATORS
    )
    sort_order = models.IntegerField("Порядок сортировки", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Изображение фотоальбома"
        verbose_name_plural = "Изображения фотоальбомов"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"Изображение #{self.pk} для альбома «{self.gallery}»"


class OrganizationInfo(models.Model):
    """
    Редактируемая информация об организации (раздел 19.6 ТЗ — желательное).
    Используется на странице AboutUs. Singleton-сущность (одна запись).
    """

    name = models.CharField("Название организации", max_length=255)
    goals = models.TextField("Цели", blank=True)
    about = models.TextField("История / О нас", blank=True)
    contacts = models.TextField("Контакты", blank=True)
    vk_url = models.URLField("VK", blank=True)
    telegram_url = models.URLField("Telegram", blank=True)
    email = models.EmailField("Email", blank=True)
    website_url = models.URLField("Сайт", blank=True)
    footer_documents_text = models.TextField("Текст документов в футере", blank=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Информация об организации"
        verbose_name_plural = "Информация об организации"

    def __str__(self) -> str:
        return self.name or "Информация об организации"

    def save(self, *args, **kwargs):
        # Singleton: всегда одна запись с pk=1.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"name": "Run With Love"})
        return obj


class TeamMember(models.Model):
    """Член команды проекта (раздел «Команда» — из письма заказчика)."""

    name = models.CharField("Имя", max_length=255)
    role = models.CharField("Роль / должность", max_length=255, blank=True)
    photo = models.ImageField(
        "Фото", upload_to="team/", null=True, blank=True, validators=IMAGE_VALIDATORS
    )
    description = models.TextField("Описание", blank=True)
    sort_order = models.IntegerField("Порядок сортировки", default=0)
    is_visible = models.BooleanField("Отображать на сайте", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Член команды"
        verbose_name_plural = "Команда"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Achievement(models.Model):
    """
    Достижение/показатель для блока «Наше влияние».
    Например: value="2 111 503 ₽", label="Собрано для помощи животным".
    Сумм по конкретным благополучателям не хранит (это общий показатель проекта).
    """

    value = models.CharField("Значение", max_length=100, help_text='Например: "2 111 503 ₽"')
    label = models.CharField("Подпись", max_length=255, help_text='Например: "Собрано для помощи"')
    sort_order = models.IntegerField("Порядок сортировки", default=0)
    is_visible = models.BooleanField("Отображать на сайте", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения (Наше влияние)"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"{self.value} — {self.label}"


class Report(models.Model):
    """
    Отчёт проекта (например, «Как использованы собранные средства»).
    Это публичная информационная сущность — без реквизитов и платёжных данных
    (раздел 12 ТЗ). Можно приложить файл (PDF) и/или указать внешнюю ссылку.
    """

    title = models.CharField("Заголовок", max_length=255)
    slug = models.SlugField("Slug (ЧПУ)", max_length=255, unique=True, blank=True)
    description = models.TextField("Описание", blank=True)
    date = models.DateField("Дата отчёта", null=True, blank=True)
    document = models.FileField(
        "Файл отчёта (PDF и т.п.)",
        upload_to="reports/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png"]
            )
        ],
        help_text="Необязательно. Можно загрузить файл и/или указать внешнюю ссылку ниже.",
    )
    external_url = models.URLField(
        "Внешняя ссылка на отчёт", blank=True,
        help_text="Необязательно. Ссылка на отчёт во внешнем сервисе.",
    )
    race = models.ForeignKey(
        "Race",
        related_name="reports",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Связанный забег",
        help_text="Необязательно. Если отчёт относится к конкретному забегу.",
    )
    sort_order = models.IntegerField("Порядок сортировки", default=0)
    is_visible = models.BooleanField("Отображать на сайте", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Отчёт"
        verbose_name_plural = "Отчёты"
        ordering = ["sort_order", "-date", "-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _unique_slug(Report, self.title)
        super().save(*args, **kwargs)


# Карта транслитерации кириллицы в латиницу для человеко-понятных URL (ЧПУ).
_TRANSLIT_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _transliterate(value: str) -> str:
    """Превращает кириллицу в латиницу, чтобы slug был читаемым (а не пустым)."""
    result = []
    for ch in (value or ""):
        lower = ch.lower()
        if lower in _TRANSLIT_MAP:
            translit = _TRANSLIT_MAP[lower]
            result.append(translit.upper() if ch.isupper() else translit)
        else:
            result.append(ch)
    return "".join(result)


def _unique_slug(model_cls, value: str) -> str:
    """Генерирует уникальный человеко-понятный slug (с транслитерацией кириллицы)."""
    base = slugify(_transliterate(value)) or "item"
    slug = base
    counter = 2
    while model_cls.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug
