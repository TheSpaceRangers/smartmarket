from decimal import Decimal

import pytest
from django.db import IntegrityError

from catalog.models import Category, Product


@pytest.mark.django_db
def test_unique_category_slug_constraint():
    c = Category.objects.create(name="Livres", slug="livres")
    Product.objects.create(category=c, name="A", slug="a", price=Decimal("1.00"))

    with pytest.raises(IntegrityError):
        Product.objects.create(category=c, name="B", slug="a", price=Decimal("2.00"))
