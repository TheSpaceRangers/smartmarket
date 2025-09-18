from __future__ import annotations

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexityValidator:
    """
    Exige: min 12 (réglé via MinimumLengthValidator), au moins 1 minuscule, 1 majuscule,
    1 chiffre et 1 caractère spécial.
    """

    def validate(self, password: str, user=None):
        if not re.search(r"[a-z]", password):
            raise ValidationError(_("Le mot de passe doit contenir au moins une minuscule."), code="password_no_lower")
        if not re.search(r"[A-Z]", password):
            raise ValidationError(_("Le mot de passe doit contenir au moins une majuscule."), code="password_no_upper")
        if not re.search(r"[0-9]", password):
            raise ValidationError(_("Le mot de passe doit contenir au moins un chiffre."), code="password_no_digit")
        if not re.search(r"[^\w\s]", password):
            raise ValidationError(_("Le mot de passe doit contenir au moins un caractère spécial."), code="password_no_symbol")

    def get_help_text(self):
        return _("Le mot de passe doit contenir des minuscules, majuscules, chiffres et symboles.")


class HIBPPasswordValidator:
    """
    Simule un contrôle HIBP: rejette une liste de mots de passe communs/fréquemment compromis.
    Ne réalise pas d’appel externe.
    """

    COMMON = {
        "password",
        "123456",
        "12345678",
        "qwerty",
        "azerty",
        "admin",
        "welcome",
        "letmein",
        "monmotdepasse",
        "motdepasse",
        "iloveyou",
        "dragon",
        "shadow",
        "football",
        "baseball",
    }

    def validate(self, password: str, user=None):
        if password.lower() in self.COMMON:
            raise ValidationError(_("Ce mot de passe est trop commun/compromis."), code="password_pwned_simulated")

    def get_help_text(self):
        return _("Le mot de passe ne doit pas être commun/compromis (contrôle simulé).")
