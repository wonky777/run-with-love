"""URL публичного API приложения content (раздел 9 ТЗ)."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BeneficiaryViewSet,
    GalleryViewSet,
    NewsViewSet,
    OrganizationInfoView,
    PartnerViewSet,
    RaceViewSet,
    TeamMemberViewSet,
    AchievementViewSet,
)

router = DefaultRouter()
router.register("races", RaceViewSet, basename="race")
router.register("news", NewsViewSet, basename="news")
router.register("partners", PartnerViewSet, basename="partner")
router.register("beneficiaries", BeneficiaryViewSet, basename="beneficiary")
router.register("galleries", GalleryViewSet, basename="gallery")
router.register("team", TeamMemberViewSet, basename="team")
router.register("achievements", AchievementViewSet, basename="achievement")

urlpatterns = [
    path("organization/", OrganizationInfoView.as_view(), name="organization"),
    path("", include(router.urls)),
]
