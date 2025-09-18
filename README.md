## SmartMarket — TP‑02 API publique + Comptes & RGPD

### Objectif

Fournir une API REST documentée pour `Category`, `Product`, `Order` avec authentification, RBAC, throttling, contrôles de sécurité et mécanismes RGPD (export/suppression). Pagination, filtres/tri, schéma OpenAPI + Swagger.

### Stack & structure

- Django 5, Python 3.11+
- DRF, django-filter, drf-spectacular, CORS Headers
- Postgres via Docker Compose
- Séparation settings: `config/settings/base.py`, `dev.py`, `prod.py`
- Qualité: black, ruff — Tests: pytest/pytest‑django/pytest‑cov

```text
smartmarket/
  compose.yaml
  pyproject.toml
  makefile
  openapi.yaml                # Schéma OpenAPI exporté
  src/
    config/                   # settings, urls, wsgi/asgi
    catalog/                  # modèles, api, permissions, serializers, tests
    templates/                # UI (liste/détail produits)
    static/
```

## Prérequis

- Python 3.11+
- Docker + Docker Compose v2 (`docker compose`)
- make

## Installation & démarrage

1. Dépendances Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

2. Variables d’environnement (exemple)

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

3. Base de données (Docker) et migrations

```bash
make up
make migrate
```

4. Données de démo et rôles (RBAC)

```bash
make seed-demo        # Catégories/produits
make seed-rbac        # Groupes client/manager/admin + users de démo
```

Utilisateurs créés (après `make seed-rbac`) :

- `admin / Admin123!Admin` (superuser)
- `manager / Manager123!$` (staff)
- `client / Client123!$`

5. Lancer le serveur

```bash
make dev
```

Application: `http://127.0.0.1:8000/`

## API publique (versionnée /api/v1/)

- `GET /api/v1/categories/` — liste (public) — filtres: recherche `name, slug`, tri `name`
- `GET /api/v1/categories/{id}/` — détail (public)
- `GET /api/v1/products/` — liste (public) — filtres: `category, is_active` — recherche `name, slug, category__name` — tri `name, price, updated_at`
- `GET /api/v1/products/{slug}/` — détail (public)
- `POST/PATCH/DELETE /api/v1/products/…` — réservé staff (`manager`/`admin`)
- `GET /api/v1/orders/` — authentifié — chaque utilisateur ne voit que ses commandes; staff voit tout
- `POST /api/v1/orders/` — crée une commande pour l’utilisateur courant
- `GET /api/v1/orders/{id}/` — authentifié — propriétaire ou staff

### Authentification

- Par défaut: DRF Session + Basic + JWT (voir `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES`).
- Classes actives: `JWTAuthentication`, `SessionAuthentication`, `BasicAuthentication`.
- Endpoint Basic (vérification): `POST /api/v1/login/` — nécessite l’en‑tête `Authorization: Basic ...`, renvoie 200 si valide.
- Endpoints JWT (cookies):
  - `POST /api/v1/jwt/login/` — Body JSON `{ "username", "password" }`. Émet des cookies HttpOnly `access_token` (~30 min) et `refresh_token` (~1 jour). Rotation + blacklist activées.
  - `POST /api/v1/jwt/refresh/` — lit le cookie `refresh_token`, émet un nouveau couple cookies.
  - `POST /api/v1/jwt/logout/` — supprime les cookies.
- Throttle `login`: 10/min. Après ≥3 échecs consécutifs au JWT login, réponse `401` puis `429` avec en‑tête `Retry-After`.
- Pour les flux session, utiliser `/api-auth/login/` (DRF) si activé.

Notes:

- Les tokens JWT sont émis en cookies HttpOnly; en production, ils sont `Secure` et `SameSite=Lax`.
- DRF lit le JWT via l’en‑tête `Authorization: Bearer <access>` (pas depuis le cookie par défaut). Le refresh/logout, eux, s’appuient sur les cookies.

### RBAC (Groupes & permissions)

- Groupes: `client`, `manager`, `admin` (commande: `make seed-rbac`).
- `client`: lecture catalogue, gestion de ses propres commandes.
- `manager`/`admin`: CRUD sur catalogue et supervision globale des commandes.

### RGPD

- Export: `GET /api/v1/me/export/` (authentifié, scope throttle `rgpd`)
- Suppression logique: `POST /api/v1/me/erase/` — désactive le compte, anonymise l’email, supprime les commandes de l’utilisateur; journalise l’opération.

### Throttling

- Global anonyme: `60/min`
- Global authentifié: `120/min`
- Sensibles: `login` et `rgpd`: `10/min`

### CORS & Sécurité web

- CORS (dev): whitelist `http://localhost:5173`, `http://127.0.0.1:5173` (voir `CORS_ALLOWED_ORIGINS`).
- CSRF actif pour les flux session.
- Production (`config/settings/prod.py`): HSTS, cookies `Secure`, `X_FRAME_OPTIONS=DENY`, `SECURE_REFERRER_POLICY`, `SECURE_CONTENT_TYPE_NOSNIFF`.

### Politiques de mot de passe

- Longueur minimale: 12 caractères.
- Complexité: au moins 1 minuscule, 1 majuscule, 1 chiffre, 1 symbole.
- Vérification « HIBP » simulée: rejet de mots de passe communs (aucun appel externe).

### Sécurité (prod)

- `DEBUG=False`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`
- HSTS: `SECURE_HSTS_SECONDS=31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS=True`, `SECURE_HSTS_PRELOAD=True`
- En‑têtes: `X_FRAME_OPTIONS=DENY`, `SECURE_REFERRER_POLICY=strict-origin-when-cross-origin`, `SECURE_CONTENT_TYPE_NOSNIFF=True`

## Documentation OpenAPI

- Schéma: `GET /api/schema/`
- Swagger UI: `GET /api/docs/`
- Fichier: `openapi.yaml` fourni à la racine (généré avec drf‑spectacular).

## Exemples d’appels (curl)

Liste produits (public):

```bash
curl -s http://127.0.0.1:8000/api/v1/products/ | jq .
```

CRUD produit (manager):

```bash
# créer
curl -u manager:manager -H 'Content-Type: application/json' \
  -d '{"name":"Livre X","slug":"livre-x","price":"12.50","stock":5,"is_active":true,"category":1}' \
  -X POST http://127.0.0.1:8000/api/v1/products/

# modifier
curl -u manager:manager -H 'Content-Type: application/json' \
  -d '{"price":"14.00"}' -X PATCH http://127.0.0.1:8000/api/v1/products/livre-x/

# supprimer
curl -u manager:manager -X DELETE http://127.0.0.1:8000/api/v1/products/livre-x/
```

Commandes utilisateur:

```bash
# lister ses commandes
curl -u client:client http://127.0.0.1:8000/api/v1/orders/

# créer une commande
curl -u client:client -H 'Content-Type: application/json' -d '{"status":"pending"}' \
  -X POST http://127.0.0.1:8000/api/v1/orders/
```

Authentification:

```bash
# Basic vers l’endpoint de vérification
curl -i -X POST -u 'client:Client123!$' http://127.0.0.1:8000/api/v1/login/

# JWT: login (JSON) → émet des cookies access/refresh
curl -i -X POST 'http://127.0.0.1:8000/api/v1/jwt/login/' \
  -H 'Content-Type: application/json' \
  -d '{"username":"client","password":"Client123!$"}'

# JWT: refresh (lit le cookie refresh_token)
curl -i -X POST 'http://127.0.0.1:8000/api/v1/jwt/refresh/'

# JWT: logout (supprime les cookies)
curl -i -X POST 'http://127.0.0.1:8000/api/v1/jwt/logout/'
```

RGPD:

```bash
# export
curl -u client:client http://127.0.0.1:8000/api/v1/me/export/

# suppression logique
curl -u client:client -X POST http://127.0.0.1:8000/api/v1/me/erase/
```

## Tests & couverture

Lancer la suite:

```bash
make test
```

Couverture (rapport terminal):

```bash
make coverage
```

La batterie inclut: authentification (succès/échec), permissions (rôles et niveau objet sur `orders`), throttling (429), RGPD export/suppression, contrats (`400/403/404`).

## Qualité de code

```bash
make lint   # ruff
make fmt    # black + corrections ruff
```

## Scénarios de vérification (avant remise)

- Lecture publique du catalogue OK; mutation anonyme refusée.
- `client` ne voit que ses commandes; `manager/admin` voient et gèrent tout.
- Throttling: `login` et `rgpd` → 429 après 10 requêtes/min.
- Documentation: Swagger ouvert; réponses concordantes avec le schéma.
- Captures à fournir:
  - Swagger UI avec endpoints et modèles
  - Résultat d’un export RGPD utilisateur
  - Refus d’accès à une commande d’un autre utilisateur (403/404)

## Notes de conception

- Pagination par défaut: 12 éléments/page (PageNumberPagination).
- Minimisation RGPD: export limité aux champs nécessaires; suppression logique + anonymisation.
- Gestion d’erreurs: codes HTTP cohérents via DRF; messages sobres (pas d’internals).

## Dépendances & outils

- Runtime: Django 5, DRF 3.15, SimpleJWT 5.3, django-filter 24.2, cors-headers 4.4, psycopg2-binary 2.9
- Dev: django-debug-toolbar, pytest/pytest-django/pytest-cov, black, ruff

## Docker Compose

- Base de données Postgres 16 exposée sur `5432`, variables via `compose.yaml` (avec healthcheck).

## Debug

- En dev: `debug_toolbar` activable, accessible via `__debug__/`.
