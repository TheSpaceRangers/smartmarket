from django.core.management.base import BaseCommand
from ml.products_index import build_index

class Command(BaseCommand):
    help = "Construit l'index vectoriel des produits (TF-IDF)."

    def add_arguments(self, parser):
        parser.add_argument("--idx-version", dest="idx_version", type=str, default=None)

    def handle(self, *args, **opts):
        idx = build_index(version=opts.get("idx_version"))
        self.stdout.write(self.style.SUCCESS(f"Product index built: version={idx.version}, dim={idx.X.shape[1]}, n={idx.ids.size}"))