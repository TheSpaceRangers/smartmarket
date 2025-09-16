from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import Category, Product


class Command(BaseCommand):
    help = "Crée des catégories/produits de démonstration"

    def handle(self, *args, **opts):
        cat_livres, _ = Category.objects.get_or_create(name="Livres", defaults={"slug": "livres"})
        cat_elec, _ = Category.objects.get_or_create(name="Électronique", defaults={"slug": "electronique"})
        items = [
            ("Django 5 en pratique", cat_livres, "Un guide concis.", Decimal("39.90")),
            ("Casque Bluetooth X200", cat_elec, "Son clair.", Decimal("79.00")),
        ]

        for name, cat, desc, price in items:
            Product.objects.get_or_create(
                name=name,
                category=cat,
                slug=name.lower().replace(" ", "-"),
                defaults={"description": desc, "price": price, "stock": 10},
            )

        self.stdout.write(self.style.SUCCESS("Données de démo créées"))
