"""Формы админки: мульти-загрузка изображений и редактор текста CKEditor 5."""

from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Gallery, News, Race, Beneficiary, Partner, OrganizationInfo


# --- Мульти-загрузка файлов (Django 5) ---
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(d, initial) for d in data if d]
        return [single(data, initial)] if data else []


def ck(name):
    """Поле с CKEditor 5 (необязательное)."""
    return forms.CharField(
        required=False,
        widget=CKEditor5Widget(config_name="default"),
        label=name,
    )


class GalleryAdminForm(forms.ModelForm):
    description = ck("Описание")
    upload_images = MultipleFileField(
        required=False, label="Загрузить несколько фото сразу"
    )

    class Meta:
        model = Gallery
        fields = "__all__"


class NewsAdminForm(forms.ModelForm):
    text = ck("Текст")
    upload_images = MultipleFileField(
        required=False, label="Загрузить несколько фото сразу"
    )

    class Meta:
        model = News
        fields = "__all__"


class RaceAdminForm(forms.ModelForm):
    short_description = ck("Краткое описание")
    description = ck("Полное описание")

    class Meta:
        model = Race
        fields = "__all__"


class BeneficiaryAdminForm(forms.ModelForm):
    description = ck("Описание")

    class Meta:
        model = Beneficiary
        fields = "__all__"


class PartnerAdminForm(forms.ModelForm):
    description = ck("Описание")

    class Meta:
        model = Partner
        fields = "__all__"


class OrganizationInfoAdminForm(forms.ModelForm):
    goals = ck("Цели")
    about = ck("История / О нас")

    class Meta:
        model = OrganizationInfo
        fields = "__all__"
