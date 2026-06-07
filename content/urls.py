"""URL публичного API приложения content (раздел 9 ТЗ)."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from .views import (
    BeneficiaryViewSet,
    GalleryViewSet,
    NewsViewSet,
    OrganizationInfoView,
    PartnerViewSet,
    RaceViewSet,
    TeamMemberViewSet,
    AchievementViewSet,
    RaceDistanceViewSet,
    NewsImageViewSet,
    GalleryImageViewSet,
)

router = DefaultRouter()
router.register("races", RaceViewSet, basename="race")
router.register("news", NewsViewSet, basename="news")
router.register("partners", PartnerViewSet, basename="partner")
router.register("beneficiaries", BeneficiaryViewSet, basename="beneficiary")
router.register("galleries", GalleryViewSet, basename="gallery")
router.register("team", TeamMemberViewSet, basename="team")
router.register("achievements", AchievementViewSet, basename="achievement")
router.register("distances", RaceDistanceViewSet, basename="distance")
router.register("news-images", NewsImageViewSet, basename="newsimage")
router.register("gallery-images", GalleryImageViewSet, basename="galleryimage")

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("organization/", OrganizationInfoView.as_view(), name="organization"),
    path("token/", obtain_auth_token, name="api_token"),
    path("", include(router.urls)),
]
