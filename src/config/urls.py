"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from catalog.api import (
    AssistantAskView,
    CategoryViewSet,
    JWTLoginView,
    JWTLogoutView,
    JWTRefreshView,
    LoginView,
    MeEraseView,
    MeExportView,
    MetricsView,
    OrderViewSet,
    PasswordResetRequestView,
    ProductRecommendationsView,
    ProductViewSet,
    RecommendationClickView,
    SearchView,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="api-category")
router.register(r"products", ProductViewSet, basename="api-product")
router.register(r"orders", OrderViewSet, basename="api-order")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("catalog.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("api/v1/", include(router.urls)),
    path("api/v1/products/<int:pk>/recommendations/", ProductRecommendationsView.as_view(), name="api-product-recommendation"),
    path("api/v1/search/", SearchView.as_view(), name="api-search"),
    path("api/v1/assistant/ask/", AssistantAskView.as_view(), name="api-assistant-ask"),
    path("api/v1/recommendations/clicks/", RecommendationClickView.as_view(), name="api-reco-click"),
    path("api/v1/metrics/", MetricsView.as_view(), name="api-metrics"),
    path("api/v1/me/export/", MeExportView.as_view(), name="api-me-export"),
    path("api/v1/me/erase/", MeEraseView.as_view(), name="api-me-erase"),
    path("api/v1/login/", LoginView.as_view(), name="api-login"),
    path("api/v1/password-reset/", PasswordResetRequestView.as_view(), name="api-password-reset"),
    path("api/v1/jwt/login/", JWTLoginView.as_view(), name="api-jwt-login"),
    path("api/v1/jwt/refresh/", JWTRefreshView.as_view(), name="api-jwt-refresh"),
    path("api/v1/jwt/logout/", JWTLogoutView.as_view(), name="api-jwt-logout"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
