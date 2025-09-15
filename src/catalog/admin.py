from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "is_active", "stock", "updated_at")
    list_filter = ("is_active", "category")
    search_fields = ("name", "slug", "category__name")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    list_select_related = ("category",)
    actions = ["activate", "deactivate"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category")

    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} produit(s) activé(s).")

    activate.short_description = "Activer les produits sélectionnés"

    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} produit(s) désactivé(s).")

    deactivate.short_description = "Désactiver les produits sélectionnés"
