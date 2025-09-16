from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from catalog.models import Category, Product

ROLE_PERMS = {
    "client": [
        ("view", Category),
        ("view", Product),
    ],
    "manager": [
        ("view", Product),
        ("add", Product),
        ("change", Product),
        ("delete", Product),
        ("view", Category),
        ("add", Category),
        ("change", Category),
        ("delete", Category),
    ],
    "admin": "all",
}

def _perm(codename_prefix: str, model):
    ct = ContentType.objects.get_for_model(model)
    return Permission.objects.get(content_type=ct, codename=f"{codename_prefix}_{model._meta.model_name}")

class Command(BaseCommand):
    help = "Crée les groupes (client/manager/admin) + utilisateurs de démo et assigne les permissions."

    def handle(self, *args, **opts):
        for role, perms in ROLE_PERMS.items():
            g, _ = Group.objects.get_or_create(name=role)
            if perms == "all":
                continue
            g.permissions.clear()
            for pfx, model in perms:
                g.permissions.add(_perm(pfx, model))
            g.save()
            self.stdout.write(self.style.SUCCESS(f"Groupe {role} prêt"))

        users = [
            ("admin", "admin", True, ["admin"]),
            ("manager", "manager", False, ["manager"]),
            ("client", "client", False, ["client"]),
        ]
        
        for username, password, is_superuser, groups in users:
            u, created = User.objects.get_or_create(username=username, defaults={"is_staff": True})
            u.set_password(password)
            u.is_superuser = is_superuser
            u.is_staff = True
            u.save()
            u.groups.clear()
            for g in groups:
                u.groups.add(Group.objects.get(name=g))
            self.stdout.write(self.style.SUCCESS(f"Utilisateur {username} ({'superuser' if is_superuser else ','.join(groups)}) prêt"))

        self.stdout.write(self.style.SUCCESS("RBAC bootstrap terminé."))