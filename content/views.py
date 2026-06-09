"""
API (раздел 9 ТЗ + CRUD).

- GET (список/деталь) — публично, без авторизации; видны только is_visible=True.
- POST/PUT/PATCH/DELETE — только по токену (IsAuthenticatedOrReadOnly).
  Авторизованному пользователю видны все записи (включая скрытые).
- Чтение отдают «read»-сериализаторы (вложенные объекты, абсолютные URL картинок),
  запись принимают «write»-сериализаторы.
"""

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import (
    Beneficiary,
    Gallery,
    News,
    Partner,
    Race,
    OrganizationInfo,
    TeamMember,
    Achievement,
    RaceDistance,
    NewsImage,
    GalleryImage,
    Report,
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
    RaceWriteSerializer,
    NewsWriteSerializer,
    PartnerWriteSerializer,
    BeneficiaryWriteSerializer,
    GalleryWriteSerializer,
    TeamMemberWriteSerializer,
    AchievementWriteSerializer,
    RaceDistanceCRUDSerializer,
    NewsImageCRUDSerializer,
    GalleryImageCRUDSerializer,
    ReportSerializer,
    ReportWriteSerializer,
)


class VisibilityMixin:
    """Публике — только is_visible=True; авторизованному — все записи."""

    read_serializer = None
    write_serializer = None

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return self.write_serializer
        return self.read_serializer

    def _visible(self, qs):
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            return qs
        return qs.filter(is_visible=True)


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class RaceViewSet(VisibilityMixin, viewsets.ModelViewSet):
    """Забеги. GET — публично; запись — по токену."""

    read_serializer = RaceSerializer
    write_serializer = RaceWriteSerializer

    def get_queryset(self):
        return self._visible(
            Race.objects.all().prefetch_related("distances", "partners", "beneficiaries")
        )


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class NewsViewSet(VisibilityMixin, viewsets.ModelViewSet):
    read_serializer = NewsSerializer
    write_serializer = NewsWriteSerializer

    def get_queryset(self):
        return self._visible(News.objects.all().prefetch_related("images"))


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class PartnerViewSet(VisibilityMixin, viewsets.ModelViewSet):
    read_serializer = PartnerSerializer
    write_serializer = PartnerWriteSerializer

    def get_queryset(self):
        return self._visible(Partner.objects.all())


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class BeneficiaryViewSet(VisibilityMixin, viewsets.ModelViewSet):
    read_serializer = BeneficiarySerializer
    write_serializer = BeneficiaryWriteSerializer

    def get_queryset(self):
        return self._visible(Beneficiary.objects.all())


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class GalleryViewSet(VisibilityMixin, viewsets.ModelViewSet):
    read_serializer = GallerySerializer
    write_serializer = GalleryWriteSerializer

    def get_queryset(self):
        return self._visible(
            Gallery.objects.all().select_related("race").prefetch_related("images")
        )


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class TeamMemberViewSet(VisibilityMixin, viewsets.ModelViewSet):
    read_serializer = TeamMemberSerializer
    write_serializer = TeamMemberWriteSerializer

    def get_queryset(self):
        return self._visible(TeamMember.objects.all())


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class AchievementViewSet(VisibilityMixin, viewsets.ModelViewSet):
    read_serializer = AchievementSerializer
    write_serializer = AchievementWriteSerializer

    def get_queryset(self):
        return self._visible(Achievement.objects.all())


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class ReportViewSet(VisibilityMixin, viewsets.ModelViewSet):
    """Отчёты проекта. GET — публично; запись — по токену."""

    read_serializer = ReportSerializer
    write_serializer = ReportWriteSerializer

    def get_queryset(self):
        return self._visible(Report.objects.all().select_related("race"))


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class RaceDistanceViewSet(viewsets.ModelViewSet):
    """Дистанции забегов. GET — публично; запись — по токену."""

    serializer_class = RaceDistanceCRUDSerializer
    queryset = RaceDistance.objects.all().select_related("race")


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class NewsImageViewSet(viewsets.ModelViewSet):
    """Изображения новостей. GET — публично; запись — по токену."""

    serializer_class = NewsImageCRUDSerializer
    queryset = NewsImage.objects.all().select_related("news")


@extend_schema_view(
    list=extend_schema(auth=[]),
    retrieve=extend_schema(auth=[]),
)
class GalleryImageViewSet(viewsets.ModelViewSet):
    """Изображения фотоальбомов. GET — публично; запись — по токену."""

    serializer_class = GalleryImageCRUDSerializer
    queryset = GalleryImage.objects.all().select_related("gallery")


class OrganizationInfoView(APIView):
    """GET /api/organization/ — информация об организации (для AboutUs)."""

    serializer_class = OrganizationInfoSerializer

    @extend_schema(responses=OrganizationInfoSerializer)
    def get(self, request):
        info = OrganizationInfo.load()
        serializer = OrganizationInfoSerializer(info, context={"request": request})
        return Response(serializer.data)
