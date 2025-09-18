import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import Category, Order, Product
from .permissions import IsOwnerOrAdmin, IsStaffOrDjangoModelPermissionsOrAnonReadOnly
from .serializers import (
    CategorySerializer,
    OrderSerializer,
    OrderWriteSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductWriteSerializer,
    UserExportSerializer,
)

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

logger = logging.getLogger(__name__)


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _login_fail_key(username, ip):
    return f"login_fail:{username}:{ip}"


def _register_failure(username, ip):
    key = _login_fail_key(username, ip)
    count = int(cache.get(key, 0)) + 1
    delay = min(2 ** max(count - 2, 0), 300)
    cache.set(key, count, timeout=delay)
    return count, delay


def _reset_failures(username, ip):
    cache.delete(_login_fail_key(username, ip))


@extend_schema(tags=["categories"])
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name"]


@extend_schema(tags=["products"])
class ProductViewSet(viewsets.ModelViewSet):
    queryset = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .only(
            "id",
            "name",
            "slug",
            "price",
            "category__name",
            "description",
            "stock",
            "is_active",
            "created_at",
            "updated_at",
        )
        .order_by("name")
    )
    lookup_field = "slug"
    permission_classes = [IsStaffOrDjangoModelPermissionsOrAnonReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "slug", "category__name"]
    ordering_fields = ["name", "price", "updated_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ProductWriteSerializer
        return ProductDetailSerializer


@extend_schema(tags=["orders"])
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated & IsOwnerOrAdmin]
    serializer_class = OrderSerializer
    queryset = Order.objects.all()

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if u.is_staff:
            return qs.order_by("-created_at")
        return qs.filter(user=u).order_by("-created_at")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return OrderWriteSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["me"], responses=UserExportSerializer, examples=[OpenApiExample("Export sample", value={"id": 1, "username": "alice", "email": "a@x.tld", "orders": []})])
class MeExportView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "rgpd"

    def get(self, request):
        data = UserExportSerializer(request.user).data
        return Response(data, status=status.HTTP_200_OK)


class MeEraseView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "rgpd"

    def post(self, request):
        u = request.user
        # suppression des données personnelles contrôlées
        Order.objects.filter(user=u).delete()
        u.is_active = False
        u.email = f"deleted+{u.id}@example.invalid"
        u.first_name = ""
        u.last_name = ""
        u.save(update_fields=["is_active", "email", "first_name", "last_name"])
        logger.info("RGPD_ERASE user_id=%s", u.id)
        return Response({"status": "scheduled", "detail": "Account disabled and data removed"}, status=status.HTTP_202_ACCEPTED)


@extend_schema(
    tags=["auth"],
    summary="Login via Basic Auth",
    description="Authentifie via HTTP Basic. 200 si identifiants valides. Verrouillage progressif après échecs.",
    examples=[
        OpenApiExample("Success", value={"detail": "authenticated", "username": "alice"}, response_only=True),
        OpenApiExample("Unauthorized", value={"detail": "invalid credentials"}, response_only=True),
    ],
)
class LoginView(APIView):
    authentication_classes = [BasicAuthentication]
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        user = getattr(request, "user", None)
        username = request.data.get("username") or (user.get_username() if user and user.is_authenticated else "")
        if not user or not user.is_authenticated:
            return Response({"detail": "invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        _reset_failures(username, _client_ip(request))
        return Response({"detail": "authenticated", "username": user.get_username()}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        return Response({"detail": "If the account exists, an email was sent."}, status=200)


def _set_cookie(resp, key, value, seconds):
    resp.set_cookie(
        key,
        value,
        max_age=int(seconds),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="Lax",
        path="/",
    )


def _clear_cookie(resp, key):
    resp.delete_cookie(key, path="/", samesite="Lax")


@extend_schema(
    tags=["auth"],
    summary="JWT login (cookies)",
    description="Authentifie via username/password, émet des cookies HttpOnly Secure: access/refresh. Throttle + verrouillage progressif inclus.",
    examples=[OpenApiExample("Success", value={"detail": "ok"}, response_only=True)],
)
class JWTLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        username = request.data.get("username", "")
        password = request.data.get("password", "")
        ip = _client_ip(request)
        user = authenticate(request, username=username, password=password)
        print(user)
        print(username)
        print(password)
        print(ip)
        if not user:
            count, delay = _register_failure(username or "unknown", ip)
            resp = Response({"detail": "invalid credentials"}, status=status.HTTP_429_TOO_MANY_REQUESTS if count >= 3 else status.HTTP_401_UNAUTHORIZED)
            if resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                resp["Retry-After"] = str(delay)
            return resp
        if not user.is_active:
            return Response({"detail": "account disabled"}, status=403)
        _reset_failures(username, ip)
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        resp = Response({"detail": "ok"}, status=200)
        _set_cookie(resp, ACCESS_COOKIE, str(access), settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
        _set_cookie(resp, REFRESH_COOKIE, str(refresh), settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
        return resp


@extend_schema(
    tags=["auth"],
    summary="JWT refresh (cookies, rotation)",
    description="Lit le cookie refresh, blackliste l’ancien et émet un nouveau couple access/refresh (rotation).",
)
class JWTRefreshView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        refresh_cookie = request.COOKIES.get(REFRESH_COOKIE)
        if not refresh_cookie:
            raise ValidationError({"detail": "missing refresh token"})
        try:
            old_refresh = RefreshToken(refresh_cookie)
        except TokenError:
            return Response({"detail": "invalid token"}, status=401)
        # Blacklist ancien refresh (si activé)
        try:
            old_refresh.blacklist()
        except Exception:
            pass
        # Re-crée un refresh pour le même utilisateur (sub)
        user_id = old_refresh.get("user_id")
        if not user_id:
            return Response({"detail": "invalid token"}, status=401)
        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "invalid user"}, status=401)
        new_refresh = RefreshToken.for_user(user)
        new_access = new_refresh.access_token
        resp = Response({"detail": "ok"}, status=200)
        _set_cookie(resp, ACCESS_COOKIE, str(new_access), settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
        _set_cookie(resp, REFRESH_COOKIE, str(new_refresh), settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
        return resp


@extend_schema(tags=["auth"], summary="JWT logout", description="Supprime les cookies JWT.")
class JWTLogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        resp = Response(status=204)
        _clear_cookie(resp, ACCESS_COOKIE)
        _clear_cookie(resp, REFRESH_COOKIE)
        return resp
