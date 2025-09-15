from django.views.generic import DetailView, ListView

from .models import Product


class ProductListView(ListView):
    model = Product
    template_name = "catalog/product_list.html"
    paginate_by = 12

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .only("id", "name", "slug", "price", "category__name")
            .order_by("name")
        )


class ProductDetailView(DetailView):
    model = Product
    template_name = "catalog/product_detail.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related("category")
