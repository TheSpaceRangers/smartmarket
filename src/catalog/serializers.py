from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category, Order, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "slug", "price", "category"]


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "is_active",
            "created_at",
            "updated_at",
            "category",
        ]
        read_only_fields = ["created_at", "updated_at"]


class ProductWriteSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Product
        fields = ["name", "slug", "description", "price", "stock", "is_active", "category"]


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class OrderWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "status"]
        read_only_fields = ["id"]


class OrderExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "status", "created_at", "updated_at"]


class UserExportSerializer(serializers.ModelSerializer):
    orders = OrderExportSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "date_joined", "last_login", "orders"]
        read_only_fields = fields
