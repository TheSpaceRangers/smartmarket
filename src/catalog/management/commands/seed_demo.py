from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import Category, Product


class Command(BaseCommand):
    help = "Crée des catégories/produits de démonstration"

    def handle(self, *args, **opts):
        cat_livres, _ = Category.objects.get_or_create(name="Livres", defaults={"slug": "livres"})
        cat_elec, _ = Category.objects.get_or_create(name="Électronique", defaults={"slug": "electronique"})
        cat_info, _ = Category.objects.get_or_create(name="Informatique", defaults={"slug": "informatique"})
        cat_audio, _ = Category.objects.get_or_create(name="Audio", defaults={"slug": "audio"})
        cat_maison, _ = Category.objects.get_or_create(name="Maison", defaults={"slug": "maison"})
        cat_cuisine, _ = Category.objects.get_or_create(name="Cuisine", defaults={"slug": "cuisine"})
        cat_sport, _ = Category.objects.get_or_create(name="Sport", defaults={"slug": "sport"})

        items = [
            ("Django 5 en pratique", cat_livres, "Un guide concis sur Django 5 et les API.", Decimal("39.90")),
            ("Python pour les data", cat_livres, "Analyse de données, pandas et numpy.", Decimal("29.90")),
            ("Casque Bluetooth X200", cat_elec, "Son clair, autonomie 20h, Bluetooth 5.0.", Decimal("79.00")),
            ("Smartphone 5G Nova", cat_elec, "Ecran OLED 6.5 pouces, 128 Go, 5G.", Decimal("399.00")),
            ("Ecran 27 pouces IPS", cat_info, "Moniteur 27\" IPS 1440p, 75Hz, bords fins.", Decimal("199.00")),
            ("Clavier mecanique MX Brown", cat_info, "Clavier mecanique layout FR, switchs marron, retroeclairage.", Decimal("89.00")),
            ("Souris gamer 6 boutons", cat_info, "Capteur 16K DPI, RGB, poignee confortable.", Decimal("49.00")),
            ("Ordinateur portable 14\"", cat_info, "Ultrabook 14 pouces, 16 Go RAM, SSD 512 Go.", Decimal("899.00")),
            ("Casque HiFi Studio", cat_audio, "Casque filaire Hi-Res, scene sonore equilibree.", Decimal("129.00")),
            ("Enceinte portable BT", cat_audio, "Etanche IPX7, basses renforcees, 12h autonomie.", Decimal("59.00")),
            ("Barre de son 2.1", cat_audio, "HDMI ARC, caisson de basses, mode cinema.", Decimal("149.00")),
            ("Aspirateur robot Lidar", cat_maison, "Cartographie pieces, application mobile, reprise auto.", Decimal("249.00")),
            ("Lampe connectee", cat_maison, "Wi-Fi, compatible assistants vocaux, multimodes.", Decimal("29.90")),
            ("Mixeur plongeant Pro", cat_cuisine, "Puissant, 3 vitesses, pied inox.", Decimal("39.90")),
            ("Blender 1.5L", cat_cuisine, "Smoothies, glace pilée, 700W.", Decimal("69.00")),
            ("Poele antiadhesive 28cm", cat_cuisine, "Revêtement durable, compatible induction.", Decimal("24.90")),
            ("Velo de ville 7 vitesses", cat_sport, "Cadre alu, eclairage LED, porte-bagages.", Decimal("349.00")),
            ("Chaussures running", cat_sport, "Amorti confortable, semelle antiderapante.", Decimal("79.90")),
            ("Montre sport GPS", cat_sport, "Cardio, GPS, etanche 5 ATM, autonomy longue.", Decimal("129.00")),
        ]

        for name, cat, desc, price in items:
            Product.objects.get_or_create(
                name=name,
                category=cat,
                slug=name.lower().replace(" ", "-"),
                defaults={"description": desc, "price": price, "stock": 10},
            )

        self.stdout.write(self.style.SUCCESS("Données de démo créées"))
