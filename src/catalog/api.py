from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly, IsAuthenticated

from .models import Category, Order, Product
from .permissions import IsOwnerOrAdmin, IsStaffOrDjangoModelPermissionsOrAnonReadOnly
from .serializers import (
    CategorySerializer,
    OrderSerializer,
    OrderWriteSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductWriteSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name"]


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
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "is_active"]
    search_fields = ["name", "slug", "category__name"]
    ordering_fields = ["name", "price", "updated_at"]
    permission_classes = [IsStaffOrDjangoModelPermissionsOrAnonReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ProductWriteSerializer
        return ProductDetailSerializer


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
