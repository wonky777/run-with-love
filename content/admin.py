"""
Django Admin — основной инструмент управления контентом.

UX-надстройки:
- Jazzmin — современная тема (подключается через settings, без кода);
- adminsortable2 — drag-and-drop сортировка (поле sort_order);
- CKEditor 5 — редактор текста (через формы в forms.py);
- мульти-загрузка фото в новости и фотоальбомы.
"""

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html

from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin

from .forms import (
    BeneficiaryAdminForm,
    GalleryAdminForm,
    NewsAdminForm,
    OrganizationInfoAdminForm,
    PartnerAdminForm,
    RaceAdminForm,
)
from .models import (
    Beneficiary,
    Gallery,
    GalleryImage,
    News,
    NewsImage,
    OrganizationInfo,
    Partner,
    Race,
    RaceDistance,
    TeamMember,
    Achievement,
    Report,
)


# --- Массовые действия для управления видимостью ---
@admin.action(description="Показать на сайте (is_visible = True)")
def make_visible(modeladmin, request, queryset):
    updated = queryset.update(is_visible=True)
    modeladmin.message_user(request, f"Показано записей: {updated}.")


@admin.action(description="Скрыть с сайта (is_visible = False)")
def make_hidden(modeladmin, request, queryset):
    updated = queryset.update(is_visible=False)
    modeladmin.message_user(request, f"Скрыто записей: {updated}.")


def image_preview(obj, field_name="image", height=60):
    image = getattr(obj, field_name, None)
    if image:
        return format_html(
            '<img src="{}" style="height:{}px;border-radius:6px;" />', image.url, height
        )
    return "—"


# --- Инлайны (drag-and-drop) ---
class RaceDistanceInline(SortableInlineAdminMixin, admin.TabularInline):
    model = RaceDistance
    extra = 1
    fields = ["length", "age_category", "sort_order"]


class NewsImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = NewsImage
    extra = 1
    fields = ["image", "preview", "sort_order"]
    readonly_fields = ["preview"]

    @admin.display(description="Превью")
    def preview(self, obj):
        return image_preview(obj)


class GalleryImageInline(SortableInlineAdminMixin, admin.TabularInline):
    model = GalleryImage
    extra = 1
    fields = ["image", "preview", "sort_order"]
    readonly_fields = ["preview"]

    @admin.display(description="Превью")
    def preview(self, obj):
        return image_preview(obj)


# --- Забеги ---
@admin.register(Race)
class RaceAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = RaceAdminForm
    list_display = ["title", "date", "status", "is_visible"]
    list_filter = ["status", "is_visible", "date"]
    search_fields = ["title", "location_text", "description"]
    list_editable = ["is_visible"]
    date_hierarchy = "date"
    inlines = [RaceDistanceInline]
    filter_horizontal = ["partners", "beneficiaries"]
    actions = [make_visible, make_hidden]
    readonly_fields = ["cover_preview", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        ("Основное", {
            "fields": (
                "title", "slug", "date", "status",
                "short_description", "description", "location_text",
                "cover_image", "cover_preview", "is_visible",
            )
        }),
        ("Внешние ссылки", {
            "fields": (
                "russian_running_url", "results_url", "rules_url",
                "route_url", "external_info_url",
            )
        }),
        ("Координаты (для карты)", {
            "classes": ("collapse",),
            "fields": ("latitude", "longitude"),
        }),
        ("Связи", {"fields": ("partners", "beneficiaries")}),
        ("SEO", {
            "classes": ("collapse",),
            "fields": ("seo_title", "seo_description", "og_image"),
        }),
        ("Служебное", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.display(description="Текущая обложка")
    def cover_preview(self, obj):
        return image_preview(obj, "cover_image", height=120)


@admin.register(RaceDistance)
class RaceDistanceAdmin(admin.ModelAdmin):
    list_display = ["__str__", "race", "length", "age_category"]
    list_filter = ["race"]
    search_fields = ["length", "age_category"]


# --- Новости (с мульти-загрузкой фото) ---
@admin.register(News)
class NewsAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = NewsAdminForm
    list_display = ["__str__", "date", "is_visible"]
    list_filter = ["is_visible", "date"]
    search_fields = ["title", "text"]
    list_editable = ["is_visible"]
    date_hierarchy = "date"
    inlines = [NewsImageInline]
    actions = [make_visible, make_hidden]
    readonly_fields = ["created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
    change_list_template = "admin/content/news_changelist.html"
    fieldsets = (
        ("Новость", {
            "fields": (
                "title", "text", "date", "source_url",
                "upload_images", "is_visible",
            ),
            "description": (
                "Заголовок можно оставить пустым — тогда новость показывается "
                "как пост. Несколько фото загружаются полем «Загрузить несколько "
                "фото сразу». Чтобы скрыть новость с сайта — снимите галочку "
                "«Отображать на сайте»."
            ),
        }),
        ("Адрес страницы (заполнится автоматически)", {
            "classes": ("collapse",),
            "fields": ("slug",),
        }),
        ("SEO (необязательно)", {
            "classes": ("collapse",),
            "fields": ("seo_title", "seo_description", "og_image"),
        }),
        ("Служебное", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        return [
            path(
                "import-vk/",
                self.admin_site.admin_view(self.import_vk_view),
                name="content_news_import_vk",
            ),
            path(
                "import-vk-url/",
                self.admin_site.admin_view(self.import_vk_url_view),
                name="content_news_import_vk_url",
            ),
        ] + urls

    def import_vk_view(self, request):
        """Автоимпорт последних новостей из сообщества ВКонтакте (VK API)."""
        from .services.vk_api import import_latest_from_vk, VKApiError

        try:
            stats = import_latest_from_vk()
            self.message_user(
                request,
                "Загрузка из ВКонтакте: получено {fetched}, добавлено новых "
                "{created}, обновлено {updated}.".format(**stats),
                level=messages.SUCCESS,
            )
        except VKApiError as exc:
            self.message_user(request, f"Не удалось загрузить из ВК: {exc}", level=messages.ERROR)
        return redirect("admin:content_news_changelist")

    def import_vk_url_view(self, request):
        """Импорт одного поста ВКонтакте по ссылке (VK API)."""
        from .services.vk_api import import_single_post_by_url, VKApiError

        if request.method == "POST":
            url = request.POST.get("post_url", "").strip()
            try:
                res = import_single_post_by_url(url)
                verb = "добавлена" if res["result"] == "created" else "обновлена"
                self.message_user(
                    request, f"Новость из ВК {verb}.", level=messages.SUCCESS
                )
                return redirect("admin:content_news_changelist")
            except VKApiError as exc:
                self.message_user(request, f"Ошибка: {exc}", level=messages.ERROR)
        context = {
            **self.admin_site.each_context(request),
            "title": "Импортировать пост по ссылке",
            "opts": self.model._meta,
        }
        return render(request, "admin/content/import_vk_url.html", context)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        files = request.FILES.getlist("upload_images")
        start = form.instance.images.count()
        for i, f in enumerate(files):
            NewsImage.objects.create(news=form.instance, image=f, sort_order=start + i)


@admin.register(NewsImage)
class NewsImageAdmin(admin.ModelAdmin):
    list_display = ["__str__", "news", "preview"]
    list_filter = ["news"]
    readonly_fields = ["preview"]

    @admin.display(description="Превью")
    def preview(self, obj):
        return image_preview(obj)


# --- Партнёры ---
@admin.register(Partner)
class PartnerAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = PartnerAdminForm
    list_display = ["name", "logo_preview", "website_url", "is_visible"]
    list_filter = ["is_visible"]
    search_fields = ["name", "description"]
    list_editable = ["is_visible"]
    actions = [make_visible, make_hidden]
    readonly_fields = ["logo_preview", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        ("Основное", {
            "fields": (
                "name", "slug", "description", "logo", "logo_preview",
                "website_url", "is_visible",
            )
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": ("seo_title", "seo_description", "og_image"),
        }),
        ("Служебное", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.display(description="Логотип")
    def logo_preview(self, obj):
        return image_preview(obj, "logo")


# --- Благополучатели ---
@admin.register(Beneficiary)
class BeneficiaryAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = BeneficiaryAdminForm
    list_display = ["name", "logo_preview", "website_url", "is_visible"]
    list_filter = ["is_visible"]
    search_fields = ["name", "description"]
    list_editable = ["is_visible"]
    actions = [make_visible, make_hidden]
    readonly_fields = ["logo_preview", "created_at", "updated_at"]
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        ("Основное", {
            "fields": (
                "name", "slug", "description", "logo_or_photo", "logo_preview",
                "website_url", "is_visible",
            ),
            "description": (
                "ВНИМАНИЕ: запрещено добавлять реквизиты и платёжные ссылки. "
                "Допустима только ссылка на официальный сайт фонда."
            ),
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": ("seo_title", "seo_description", "og_image"),
        }),
        ("Служебное", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    @admin.display(description="Лого/фото")
    def logo_preview(self, obj):
        return image_preview(obj, "logo_or_photo")


# --- Фотоальбомы (с мульти-загрузкой фото) ---
@admin.register(Gallery)
class GalleryAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = GalleryAdminForm
    list_display = ["title", "race", "date", "is_visible"]
    list_filter = ["is_visible", "race", "date"]
    search_fields = ["title", "description"]
    list_editable = ["is_visible"]
    date_hierarchy = "date"
    inlines = [GalleryImageInline]
    actions = [make_visible, make_hidden]
    readonly_fields = ["created_at", "updated_at"]
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        ("Основное", {
            "fields": (
                "title", "slug", "description", "race", "date",
                "upload_images", "is_visible",
            )
        }),
        ("SEO", {
            "classes": ("collapse",),
            "fields": ("seo_title", "seo_description", "og_image"),
        }),
        ("Служебное", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        files = request.FILES.getlist("upload_images")
        start = form.instance.images.count()
        for i, f in enumerate(files):
            GalleryImage.objects.create(
                gallery=form.instance, image=f, sort_order=start + i
            )


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ["__str__", "gallery", "preview"]
    list_filter = ["gallery"]
    readonly_fields = ["preview"]

    @admin.display(description="Превью")
    def preview(self, obj):
        return image_preview(obj)


# --- Команда ---
@admin.register(TeamMember)
class TeamMemberAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["name", "role", "photo_preview", "is_visible"]
    list_filter = ["is_visible"]
    search_fields = ["name", "role", "description"]
    list_editable = ["is_visible"]
    actions = [make_visible, make_hidden]
    readonly_fields = ["photo_preview", "created_at", "updated_at"]

    @admin.display(description="Фото")
    def photo_preview(self, obj):
        return image_preview(obj, "photo")


# --- Достижения ---
@admin.register(Achievement)
class AchievementAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["value", "label", "is_visible"]
    list_filter = ["is_visible"]
    search_fields = ["value", "label"]
    list_editable = ["is_visible"]
    actions = [make_visible, make_hidden]


# --- Отчёты ---
@admin.register(Report)
class ReportAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ["title", "date", "race", "is_visible"]
    list_filter = ["is_visible", "race", "date"]
    search_fields = ["title", "description"]
    list_editable = ["is_visible"]
    date_hierarchy = "date"
    actions = [make_visible, make_hidden]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["race"]
    fieldsets = (
        ("Отчёт", {
            "fields": (
                "title", "description", "date",
                "document", "external_url", "race", "is_visible",
            ),
            "description": (
                "Можно загрузить файл отчёта (PDF и т.п.) и/или указать ссылку "
                "на внешний отчёт. Не указывайте здесь платёжные реквизиты."
            ),
        }),
        ("Служебное", {
            "classes": ("collapse",),
            "fields": ("created_at", "updated_at"),
        }),
    )


# --- Информация об организации (singleton) ---
@admin.register(OrganizationInfo)
class OrganizationInfoAdmin(admin.ModelAdmin):
    form = OrganizationInfoAdminForm
    list_display = ["name", "email", "updated_at"]

    def has_add_permission(self, request):
        return not OrganizationInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
