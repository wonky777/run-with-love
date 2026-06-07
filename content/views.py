"""
Публичное read-only API (раздел 9 ТЗ).

Все endpoints:
- доступны без авторизации (GET);
- отдают только записи с is_visible=True;
- возвращают абсолютные URL изображений.
"""

from rest_framework import viewsets
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import (
    Beneficiary,
    Gallery,
    News,
    Partner,
    Race,
    OrganizationInfo,
    TeamMember,
    Achievement,
)
from .serializers import (
    BeneficiarySerializer,
    GallerySerializer,
    NewsSerializer,
    PartnerSerializer,
    RaceSerializer,
    OrganizationInfoSerializer,
    TeamMemberSerializer,
    AchievementSerializer,
)


class RaceViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/races/ — список забегов с дистанциями, партнёрами, благополучателями."""

    serializer_class = RaceSerializer

    def get_queryset(self):
        return (
            Race.objects.filter(is_visible=True)
            .prefetch_related("distances", "partners", "beneficiaries")
        )


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/news/ — список новостей с галереей изображений."""

    serializer_class = NewsSerializer

    def get_queryset(self):
        return News.objects.filter(is_visible=True).prefetch_related("images")


class PartnerViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/partners/ — список партнёров."""

    serializer_class = PartnerSerializer

    def get_queryset(self):
        return Partner.objects.filter(is_visible=True)


class BeneficiaryViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/beneficiaries/ — список благополучателей."""

    serializer_class = BeneficiarySerializer

    def get_queryset(self):
        return Beneficiary.objects.filter(is_visible=True)


class GalleryViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/galleries/ — список фотоальбомов с изображениями."""

    serializer_class = GallerySerializer

    def get_queryset(self):
        return (
            Gallery.objects.filter(is_visible=True)
            .select_related("race")
            .prefetch_related("images")
        )


class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/team/ — команда проекта."""

    serializer_class = TeamMemberSerializer

    def get_queryset(self):
        return TeamMember.objects.filter(is_visible=True)


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/achievements/ — показатели для блока «Наше влияние»."""

    serializer_class = AchievementSerializer

    def get_queryset(self):
        return Achievement.objects.filter(is_visible=True)


class OrganizationInfoView(APIView):
    """GET /api/organization/ — информация об организации (для AboutUs)."""

    serializer_class = OrganizationInfoSerializer

    @extend_schema(responses=OrganizationInfoSerializer)
    def get(self, request):
        info = OrganizationInfo.load()
        serializer = OrganizationInfoSerializer(info, context={"request": request})
        return Response(serializer.data)
