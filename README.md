## SmartMarket — TP‑01

### Objectif

Socle Django prêt à l’emploi: modèles `Category`/`Product` avec contraintes et index, administration avancée, pages liste/détail, Postgres via Docker, debug toolbar, qualité de code (black, ruff), tests de base et données de démonstration.

### Aperçu technique

- Django 5, Python 3.11+
- Base Postgres (Docker Compose)
- Séparation des paramètres: `config/settings/base.py`, `dev.py`, `prod.py`
- Debug Toolbar activable en dev (`/__debug__/`)
- Qualité: black, ruff
- Tests: pytest/pytest‑django

## Prérequis

- Python 3.11+
- Docker + Docker Compose v2 (`docker compose`)
- make

## Installation

1. Cloner le dépôt puis créer l’environnement Python:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

2. Variables d’environnement: copier le modèle et adapter au besoin.

```bash
cp .env.example .env
```

3. Démarrer Postgres (Docker):

```bash
docker compose up -d db
```

4. Appliquer les migrations et données de démo:

```bash
make migrate
make seed
```

5. Lancer le serveur de dev:

```bash
make dev
```

Le site répond sur `http://127.0.0.1:8000/`.

## Paramètres et environnements

- Dev et tests utilisent `config.settings.dev` (voir `src/manage.py`, `config/asgi.py`, `config/wsgi.py`, et `pyproject.toml`).
- `base.py` configure Postgres via variables d’environnement (voir `.env.example`).
- En prod, utiliser `config.settings.prod` (sécurité: cookies, HSTS, redirect SSL, etc.).

### Exemple de `.env.example`

```env
SECRET_KEY=change-me
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=smartmarket
POSTGRES_USER=sm_user
POSTGRES_PASSWORD=sm_pass
DB_HOST=localhost
DB_PORT=5432

LANGUAGE_CODE=fr-fr
TIME_ZONE=Europe/Paris
```

## Commandes Make

Depuis la racine du projet:

```bash
make up       # Démarrer Postgres (Docker)
make migrate  # Appliquer les migrations
make seed     # Insérer des données de démonstration
make test     # Lancer la suite de tests (pytest)
make lint     # Vérification ruff
make fmt      # Formatage black + corrections ruff
make dev      # Démarrer le serveur de développement
```

## Tests

```bash
make test
```

Tests inclus:

- Contrainte d’unicité `(category, slug)`
- Vues de liste et de détail

## Debug Toolbar

- Active en développement: `http://127.0.0.1:8000/__debug__/`
- Le `urlpatterns` est protégé si la lib n’est pas installée.

## Administration

- Accès: `http://127.0.0.1:8000/admin/`
- Créer un superutilisateur si besoin:

```bash
python src/manage.py createsuperuser
```

- Admin `Product`:
  - list_display: nom, catégorie, prix, actif, stock, updated_at
  - list_filter: actif, catégorie
  - search_fields: nom, slug, catégorie
  - prepopulated_fields: slug depuis name
  - autocomplete_fields: category
  - actions: activer/désactiver
  - `list_select_related` + `get_queryset()` optimisés

## Données de démo

```bash
make seed
```

Crée deux catégories et quelques produits (voir `src/catalog/management/commands/seed_demo.py`).

## Structure du projet

```text
smartmarket/
  compose.yaml                # Service Postgres (volume + healthcheck)
  pyproject.toml              # Dépendances + config black/ruff/pytest
  makefile                    # Cibles utilitaires
  src/
    config/                   # Projet Django (settings séparés, urls, wsgi/asgi)
    catalog/                  # Application (modèles, admin, vues, urls, tests)
    templates/                # Templates globaux (base, catalog/*)
    static/                   # Assets dev
```
