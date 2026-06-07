"""
Сериализаторы публичного API.

Формат ответов строго соответствует разделу 9 ТЗ. Изображения отдаются как
абсолютные URL (build_absolute_uri через context['request']).
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import (
    Beneficiary,
    Gallery,
    GalleryImage,
    News,
    NewsImage,
    Partner,
    Race,
    RaceDistance,
    OrganizationInfo,
    TeamMember,
    Achievement,
)


# --- Партнёры (раздел 9.4) ---
class PartnerSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(use_url=True)

    class Meta:
        model = Partner
        fields = ["id", "name", "description", "logo", "website_url"]


class PartnerShortSerializer(serializers.ModelSerializer):
    """Краткая версия для вложения в забег (раздел 9.2)."""

    logo = serializers.ImageField(use_url=True)

    class Meta:
        model = Partner
        fields = ["id", "name", "logo", "website_url"]


# --- Благополучатели (раздел 9.5) ---
class BeneficiarySerializer(serializers.ModelSerializer):
    logo_or_photo = serializers.ImageField(use_url=True)

    class Meta:
        model = Beneficiary
        fields = ["id", "name", "description", "logo_or_photo", "website_url"]


class BeneficiaryShortSerializer(serializers.ModelSerializer):
    """Краткая версия для вложения в забег (раздел 9.2)."""

    logo_or_photo = serializers.ImageField(use_url=True)

    class Meta:
        model = Beneficiary
        fields = ["id", "name", "logo_or_photo", "website_url"]


# --- Дистанции (вложены в забег) ---
class RaceDistanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RaceDistance
        fields = ["id", "length", "age_category"]


# --- Забеги (раздел 9.2) ---
class RaceSerializer(serializers.ModelSerializer):
    cover_image = serializers.ImageField(use_url=True)
    distances = RaceDistanceSerializer(many=True, read_only=True)
    partners = serializers.SerializerMethodField()
    beneficiaries = serializers.SerializerMethodField()

    class Meta:
        model = Race
        fields = [
            "id",
            "title",
            "slug",
            "date",
            "status",
            "short_description",
            "description",
            "location_text",
            "cover_image",
            "russian_running_url",
            "results_url",
            "rules_url",
            "route_url",
            "external_info_url",
            "latitude",
            "longitude",
            "distances",
            "partners",
            "beneficiaries",
        ]

    @extend_schema_field(PartnerShortSerializer(many=True))
    def get_partners(self, obj):
        qs = obj.partners.filter(is_visible=True)
        return PartnerShortSerializer(qs, many=True, context=self.context).data

    @extend_schema_field(BeneficiaryShortSerializer(many=True))
    def get_beneficiaries(self, obj):
        qs = obj.beneficiaries.filter(is_visible=True)
        return BeneficiaryShortSerializer(qs, many=True, context=self.context).data


# --- Новости (раздел 9.3) ---
class NewsImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = NewsImage
        fields = ["id", "image"]


class NewsSerializer(serializers.ModelSerializer):
    images = NewsImageSerializer(many=True, read_only=True)

    class Meta:
        model = News
        fields = [
            "id",
            "title",
            "text",
            "date",
            "source_url",
            "is_from_vk",
            "images",
        ]


# --- Фотоальбомы (раздел 9.6) ---
class GalleryImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = GalleryImage
        fields = ["id", "image"]


class GalleryRaceSerializer(serializers.ModelSerializer):
    """Краткая инфо о забеге внутри альбома (раздел 9.6)."""

    class Meta:
        model = Race
        fields = ["id", "title"]


class GallerySerializer(serializers.ModelSerializer):
    images = GalleryImageSerializer(many=True, read_only=True)
    race = serializers.SerializerMethodField()

    class Meta:
        model = Gallery
        fields = ["id", "title", "description", "date", "race", "images"]

    @extend_schema_field(GalleryRaceSerializer)
    def get_race(self, obj):
        if obj.race and obj.race.is_visible:
            return GalleryRaceSerializer(obj.race, context=self.context).data
        return None


# --- Информация об организации (раздел 19.6 — желательное) ---
class OrganizationInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInfo
        fields = [
            "name",
            "goals",
            "about",
            "contacts",
            "vk_url",
            "telegram_url",
            "email",
            "website_url",
            "footer_documents_text",
        ]


# --- Команда ---
class TeamMemberSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(use_url=True)

    class Meta:
        model = TeamMember
        fields = ["id", "name", "role", "photo", "description"]


# --- Достижения (Наше влияние) ---
class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ["id", "value", "label"]


# === Сериализаторы для записи (POST/PUT/PATCH) ===
# Используются только для создания/изменения через токен. Чтение отдают
# сериализаторы выше (с вложенными объектами и абсолютными URL картинок).

class RaceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Race
        exclude = ["created_at", "updated_at"]


class NewsWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        exclude = ["created_at", "updated_at"]


class PartnerWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        exclude = ["created_at", "updated_at"]


class BeneficiaryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiary
        exclude = ["created_at", "updated_at"]


class GalleryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        exclude = ["created_at", "updated_at"]


class TeamMemberWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        exclude = ["created_at", "updated_at"]


class AchievementWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        exclude = ["created_at", "updated_at"]
