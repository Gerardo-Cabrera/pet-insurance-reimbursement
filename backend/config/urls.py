from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.claims.views import ClaimViewSet
from apps.pets.views import PetViewSet
from apps.users.views import MeView, RegisterView
from config.api_views import HealthView, TokenObtainPairSchemaView, TokenRefreshSchemaView

router = DefaultRouter()
router.register("pets", PetViewSet, basename="pet")
router.register("claims", ClaimViewSet, basename="claim")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/auth/me/", MeView.as_view(), name="auth-me"),
    path("api/token/", TokenObtainPairSchemaView.as_view(), name="token_obtain_pair"),
    path(
        "api/token/refresh/",
        TokenRefreshSchemaView.as_view(),
        name="token_refresh",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
