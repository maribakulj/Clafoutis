---
title: Clafoutis MVP
emoji: 📚
sdk: docker
app_port: 7860
short_description: Prototype federated portal for cultural heritage resources.
---

# Clafoutis

Portail universel de recherche IIIF avec lecture dans Mirador et connecteurs extensibles.

## Objectif

Cette application permet de :

- rechercher des objets patrimoniaux dans plusieurs institutions ;
- agréger et normaliser les résultats dans un format commun ;
- afficher une galerie homogène de résultats ;
- ouvrir directement les ressources dans Mirador à partir de leurs manifests IIIF ;
- comparer plusieurs objets dans le même viewer ;
- exposer les fonctions principales via une API REST ;
- prévoir une couche MCP sans duplication de logique métier.

## Vision produit

Le produit est structuré en trois couches :

1. **Découverte** : recherche fédérée multi-sources ;
2. **Lecture** : visualisation et comparaison dans Mirador ;
3. **Interopérabilité** : API interne normalisée et couche MCP optionnelle.

Principe fondamental :

> Mirador est la couche de lecture, jamais la couche de recherche.

## Périmètre MVP

Le MVP doit inclure :

- recherche fédérée sur un petit nombre de sources ;
- schéma de données normalisé ;
- galerie de résultats ;
- ouverture simple et multiple dans Mirador ;
- import manuel d’un manifest IIIF ou d’une URL de notice ;
- description des sources disponibles et de leurs capacités ;
- robustesse aux échecs partiels.

Le MVP n’inclut pas :

- compte utilisateur ;
- annotation persistante ;
- index mondial exhaustif ;
- moissonnage global du web patrimonial ;
- recherche OCR universelle.

## Stack technique

### Frontend

- React
- TypeScript
- Tailwind CSS
- TanStack Query
- Zustand ou Redux Toolkit
- Mirador

### Backend

- Python 3.11+
- FastAPI
- Pydantic
- httpx async

### Déploiement

- Docker
- Hugging Face Spaces

## Architecture du projet

```text
app/
  frontend/
    src/
      components/
      pages/
      hooks/
      store/
      lib/
      types/
  backend/
    app/
      api/
      services/
      connectors/
      models/
      mcp/
      utils/
      config/
  tests/
    unit/
    integration/
  docs/
  Dockerfile
  docker-compose.yml
  README.md
```

## Concepts importants

### Schéma normalisé

Toutes les sources externes sont transformées dans un schéma commun de type `NormalizedItem`.

Le schéma normalisé est le cœur du projet : l’interface ne doit pas dépendre directement des payloads bruts des institutions.

### Connecteurs

Chaque source est branchée via un connecteur indépendant.

Chaque connecteur doit implémenter une interface commune, par exemple :

- `search(query, filters, page, page_size)`
- `get_item(source_id)`
- `resolve_manifest(item_or_url)`
- `healthcheck()`
- `capabilities()`

### Succès partiel

Si une source échoue, les autres doivent quand même répondre.

Le moteur fédéré ne doit jamais échouer globalement à cause d’un seul connecteur.

## Fonctionnalités prévues

- recherche simple multi-sources ;
- filtres par institution, type, langue, période, disponibilité IIIF ;
- galerie homogène ;
- ouverture d’un résultat dans Mirador ;
- comparaison de plusieurs manifests ;
- import manuel d’URL ;
- page Sources avec capacités déclaratives ;
- couche MCP optionnelle.

## Endpoints backend prévus

- `GET /api/health`
- `GET /api/sources`
- `POST /api/search`
- `GET /api/item/{id}`
- `POST /api/resolve-manifest`
- `POST /api/import`

### Heuristiques MVP de `/api/import`

Le connecteur générique `manifest_by_url` applique des heuristiques minimales et explicites :

1. **Manifest direct** : l’URL est considérée comme manifest si son chemin contient `manifest`
   (ou se termine par `manifest.json`).
2. **Notice -> manifest** : si l’URL ne ressemble pas à un manifest, le backend tente des suffixes
   courants, dans cet ordre :
   - `/manifest`
   - `/manifest.json`
   - `/iiif/manifest`
   - `/iiif/manifest.json`

Ces heuristiques sont volontairement simples au MVP et seront enrichies par source aux lots
connecteurs réels.

### Sécurité MVP import URL (validation + SSRF basique)

`/api/import` applique une validation stricte avant résolution :

- schémas autorisés : `http`, `https` uniquement ;
- rejet explicite de `localhost`/hôtes locaux ;
- rejet des IP privées/loopback/link-local/réservées/unspecified ;
- rejet des hôtes DNS qui résolvent vers ces plages privées/locales.

Limite connue MVP : cette protection SSRF reste basique et devra être durcie (allowlist,
résolution DNS contrôlée, protections réseau infra) avant production.

## Outils MCP prévus

- `search_items`
- `get_item`
- `resolve_manifest`
- `open_in_mirador`
- `list_sources`

## Installation locale

### Prérequis

- Python 3.11+
- Node.js 20+ ou version définie dans le projet
- npm, pnpm ou yarn
- Docker (optionnel mais recommandé)

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --app-dir app/backend --reload
```

### Frontend

```bash
cd app/frontend
npm install
npm run dev
```

Par défaut, le frontend appelle `http://localhost:8000`.

Optionnel :

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Variables d’environnement

Créer un fichier `.env` à partir de `.env.example`.

Variables backend principales (préfixe `CLAFOUTIS_`) :

```env
CLAFOUTIS_DEBUG=false
CLAFOUTIS_APP_HOST=0.0.0.0
CLAFOUTIS_APP_PORT=7860
CLAFOUTIS_REQUEST_TIMEOUT_SECONDS=8
CLAFOUTIS_CORS_ALLOW_ORIGINS=["http://localhost:5173"]

CLAFOUTIS_SERVE_FRONTEND=true
CLAFOUTIS_FRONTEND_DIST_DIR=app/frontend/dist

CLAFOUTIS_GALLICA_USE_FIXTURES=true
CLAFOUTIS_BODLEIAN_USE_FIXTURES=true
CLAFOUTIS_EUROPEANA_USE_FIXTURES=true
CLAFOUTIS_EUROPEANA_API_KEY=

# Hugging Face Spaces: HF_TOKEN est aussi accepté en fallback pour Europeana
# (utile si votre secret Space est nommé HF_TOKEN).

CLAFOUTIS_ENABLE_CAPABILITY_PROBING=true
CLAFOUTIS_CAPABILITY_PROBE_USE_FIXTURES=true
CLAFOUTIS_CAPABILITY_PROBE_TIMEOUT_SECONDS=2
CLAFOUTIS_CAPABILITY_PROBE_CACHE_TTL_SECONDS=300
```

Pour le frontend en mode dev local (Vite séparé) :

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Packaging Docker (lot démo Hugging Face Spaces)

Stratégie MVP :

- image **unique** ;
- build frontend React dans une étape Node ;
- copie des assets `dist` dans l’image runtime Python ;
- backend FastAPI sert API + assets frontend (SPA fallback) sur un **port unique** ;
- mode fixtures activable par variables d’environnement (par défaut recommandé pour démo).

### Build image

```bash
docker build -t clafoutis-mvp .
```

### Run local (démo)

```bash
docker run --rm -p 7860:7860 \
  -e PORT=7860 \
  -e CLAFOUTIS_GALLICA_USE_FIXTURES=true \
  -e CLAFOUTIS_BODLEIAN_USE_FIXTURES=true \
  -e CLAFOUTIS_EUROPEANA_USE_FIXTURES=true \
  clafoutis-mvp
```

Puis ouvrir :

- UI : `http://localhost:7860`
- API health : `http://localhost:7860/api/health`

### Hugging Face Spaces (Docker)

1. Créer un Space de type **Docker**.
2. Pousser ce dépôt (avec `Dockerfile`) dans le Space.
3. Définir les variables du Space (Settings -> Variables), au minimum :
   - `PORT=7860`
   - `CLAFOUTIS_GALLICA_USE_FIXTURES=true`
   - `CLAFOUTIS_BODLEIAN_USE_FIXTURES=true`
   - `CLAFOUTIS_EUROPEANA_USE_FIXTURES=true`
4. Optionnel : ajouter `CLAFOUTIS_EUROPEANA_API_KEY` pour le mode live Europeana.
   Le backend accepte aussi `HF_TOKEN` en fallback si votre secret Space porte ce nom.
5. Si vous utilisez le workflow GitHub de déploiement, configurez un secret GitHub
   `HF_SPACE_TOKEN` (ou `HF_TOKEN`, désormais accepté en fallback).

Le point d’entrée est `scripts/start.sh`, qui démarre Uvicorn sur `HOST/PORT` compatibles Space Docker.

## Sources prévues pour le MVP

- Gallica / BnF
- Bodleian Digital
- Europeana
- connecteur générique `manifest-by-url`

## Connecteur Gallica (lot 5)

### Hypothèses de mapping `NormalizedItem`

- `source_item_id` : ARK extrait des identifiants Gallica (`ark:/...`) ;
- `id` global : `gallica:{source_item_id}` ;
- `title` : premier champ `dc:title` disponible ;
- `creators` : liste des `dc:creator` ;
- `date_display` : premier `dc:date` ;
- `object_type` : dérivé de `dc:type` via mapping simple (`manuscript`, `book`, `map`, `image`, `newspaper`, `other`) ;
- `record_url` : premier `dc:identifier` ;
- `manifest_url` : construit depuis l’ARK (`https://gallica.bnf.fr/iiif/{ark}/manifest.json`) ;
- `institution` : `Bibliothèque nationale de France`.

### Stratégie de résolution de manifest

1. si `item.manifest_url` est déjà présent, il est renvoyé ;
2. sinon, extraction d’un ARK depuis `record_url` (ou URL fournie) ;
3. construction déterministe de l’URL IIIF manifest Gallica.

### Robustesse / mode fallback

- Le connecteur tente un mode live SRU Gallica ;
- pour éviter de casser la suite en environnement instable, un mode fixtures est disponible (`CLAFOUTIS_GALLICA_USE_FIXTURES=true` au MVP, valeur par défaut) ;
- en cas d’échec live, le connecteur renvoie un succès dégradé avec données fixtures et `partial_failures` explicite.

### Limites connues (MVP)

- le parsing SRU est volontairement minimal et basé sur un sous-ensemble Dublin Core ;
- certains champs Gallica restent absents/incertains selon les notices ;
- la détection fine des types documentaires sera améliorée aux lots suivants.

## Connecteurs Bodleian et Europeana (lot 6)

### Bodleian — mapping `NormalizedItem`

- `source_item_id` : identifiant objet Bodleian ;
- `id` global : `bodleian:{source_item_id}` ;
- `title`, `creators`, `date_display` : extraits du payload source ou fixtures ;
- `record_url` : URL notice Bodleian (`/objects/{id}/`) ;
- `manifest_url` : prioritairement fourni, sinon construit via pattern
  `https://iiif.bodleian.ox.ac.uk/iiif/manifest/{id}.json` ;
- `institution` : `Bodleian Libraries`.

### Europeana — mapping `NormalizedItem`

- `source_item_id` : `id` Europeana ;
- `id` global : `europeana:{source_item_id}` ;
- `title`, `creators`, `date_display` : extraits du payload source ou fixtures ;
- `record_url` : `guid` Europeana (ou URL item fixture) ;
- `manifest_url` :
  - `edmIsShownBy` si manifest explicite ;
  - sinon fallback pattern `https://iiif.europeana.eu/presentation/{item_path}/manifest` ;
- `institution` : `Europeana` ou institution partenaire fixture.

### Capacités et mode robustesse

- les deux connecteurs implémentent `search`, `get_item`, `resolve_manifest`, `capabilities`, `healthcheck` ;
- stratégie **fixture-first** activée par défaut au MVP (`CLAFOUTIS_BODLEIAN_USE_FIXTURES=true`, `CLAFOUTIS_EUROPEANA_USE_FIXTURES=true`) pour préserver la stabilité ;
- en mode live, les erreurs réseau/API retombent en mode dégradé avec `partial_failures` explicites ;
- Europeana live nécessite une clé API (`CLAFOUTIS_EUROPEANA_API_KEY`).

### Limites connues (MVP)

- endpoints live Bodleian/Europeana restent best-effort et peuvent évoluer ;
- mapping conservateur pour limiter les faux positifs ;
- enrichissement sémantique (types, droits, OCR, langue fine) prévu après lot 6.

## Principes de développement

- code modulaire ;
- typage strict ;
- séparation claire frontend / backend / connecteurs ;
- aucune duplication de logique métier entre REST et MCP ;
- Mirador utilisé uniquement comme couche de lecture ;
- tests unitaires minimum sur les connecteurs ;
- tests d’intégration minimum sur les endpoints critiques.

## Ordre de développement recommandé

1. socle backend ;
2. socle frontend ;
3. intégration Mirador minimale ;
4. import manuel ;
5. connecteurs réels ;
6. ranking, cache et robustesse ;
7. couche MCP ;
8. déploiement Docker / Hugging Face Spaces.

## État du projet

Statut actuel : en cours de développement.

## Priorité actuelle

- [ ] Backend socle
- [ ] Frontend socle
- [ ] Intégration Mirador
- [ ] Import manuel
- [ ] Connecteur Gallica
- [ ] Connecteurs Bodleian et Europeana
- [ ] MCP
- [ ] Docker / déploiement HF Spaces

## Documentation

Voir aussi :

- `AGENTS.md`
- `PLANS.md`
- `docs/specs.md`

## Contribution

Avant toute contribution :

- lire `AGENTS.md` ;
- respecter l’architecture du projet ;
- ne pas dupliquer la logique métier ;
- garder les connecteurs isolés ;
- documenter clairement tout nouveau module.
