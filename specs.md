# Spécification produit et technique

## Portail universel de recherche IIIF + lecture Mirador + connecteurs MCP

## 1. Résumé exécutif

Objectif : créer une application web déployable sur un Hugging Face Space permettant de rechercher des objets patrimoniaux dans plusieurs bibliothèques et musées numériques du monde, d’afficher une galerie de résultats unifiée, puis d’ouvrir directement les objets sélectionnés dans Mirador pour lecture, comparaison et navigation.

Le produit doit être pensé comme trois couches distinctes :

1. **Couche découverte** : moteur fédéré de recherche multi-sources.
2. **Couche lecture** : viewer IIIF basé sur Mirador.
3. **Couche interopérabilité** : API interne normalisée et outils MCP permettant à un agent IA ou à un autre client de lancer une recherche, récupérer un manifest et ouvrir une ressource dans Mirador.

Le projet ne doit pas supposer que Mirador sait faire la recherche. Mirador est uniquement la couche d’affichage.

---

## 2. Vision produit

### 2.1 Problème

Aujourd’hui, les ressources IIIF sont dispersées entre de nombreuses institutions. Même quand les objets sont accessibles, l’utilisateur doit souvent :

* connaître l’institution à l’avance ;
* chercher sur plusieurs interfaces différentes ;
* comprendre des modèles de données hétérogènes ;
* récupérer manuellement les manifests ;
* changer de viewer selon l’établissement.

### 2.2 Proposition de valeur

Le produit doit offrir une expérience simple :

**Chercher partout, lire tout de suite, comparer dans le même viewer.**

### 2.3 Utilisateurs cibles

* chercheurs en histoire, histoire de l’art, philologie, humanités numériques ;
* conservateurs, documentalistes, bibliothécaires ;
* étudiants ;
* amateurs avancés ;
* développeurs IA ou agents utilisant MCP.

### 2.4 Promesse utilisateur

Un utilisateur tape une requête unique, obtient une galerie d’objets provenant de plusieurs institutions, filtre les résultats, puis ouvre un ou plusieurs objets dans Mirador sans avoir à manipuler les manifests manuellement.

---

## 3. Périmètre du MVP

Le MVP doit rester réaliste, robuste et simple à déployer.

### 3.1 Ce que le MVP doit faire

* proposer une recherche fédérée sur un petit nombre de sources initiales ;
* normaliser les résultats dans un format unique ;
* afficher une galerie de résultats ;
* ouvrir un résultat dans Mirador via son manifest IIIF ;
* permettre l’ouverture de plusieurs objets en parallèle dans Mirador ;
* exposer les fonctions principales via une API interne ;
* exposer éventuellement ces fonctions via MCP.

### 3.2 Sources initiales recommandées pour le MVP

Commencer avec 3 à 5 connecteurs maximum.

Je recommande :

* Gallica / BnF
* Bodleian Digital
* Europeana
* un connecteur générique IIIF manifest-by-URL
* éventuellement une source de démonstration simple et stable

### 3.3 Ce que le MVP ne doit pas faire

* pas de moissonnage global du web patrimonial ;
* pas d’index mondial complet ;
* pas de promesse de couverture exhaustive ;
* pas de création de compte utilisateur ;
* pas d’annotation collaborative persistante dans la première version ;
* pas de recherche plein texte universelle sur tous les OCR du monde.

---

## 4. Principes de conception

### 4.1 Architecture modulaire

Chaque source doit être branchée via un connecteur indépendant. L’ajout d’une nouvelle institution ne doit pas nécessiter de modifier le cœur applicatif.

### 4.2 Dégradation élégante

Si une source ne fournit pas toutes les métadonnées attendues, le système doit renvoyer un résultat partiel plutôt qu’un échec global.

### 4.3 Transparence

Chaque résultat doit afficher clairement :

* l’institution source ;
* le type de source ;
* l’URL de notice ;
* la disponibilité ou non d’un manifest IIIF ;
* les droits si connus.

### 4.4 IIIF-first mais pas IIIF-only

Le système privilégie les ressources IIIF, mais il doit accepter que certains catalogues aient une recherche propre et un accès au manifest indirect.

### 4.5 Viewer séparé du moteur

Mirador ne contient aucune logique de recherche métier. Il reçoit des manifests déjà identifiés par la couche découverte.

---

## 5. Cas d’usage

### 5.1 Recherche simple

L’utilisateur tape « book of hours » et voit des résultats venant de plusieurs institutions.

### 5.2 Filtrage

L’utilisateur filtre par institution, type d’objet, langue, période ou disponibilité IIIF.

### 5.3 Lecture

L’utilisateur clique sur un résultat et l’objet s’ouvre dans Mirador.

### 5.4 Comparaison

L’utilisateur sélectionne plusieurs résultats et les ouvre côte à côte dans Mirador.

### 5.5 Import manuel

L’utilisateur colle l’URL d’un manifest IIIF ou d’une notice ; le système tente de détecter le manifest et l’ouvre.

### 5.6 Usage agentique

Un agent appelle le serveur MCP pour rechercher « Dante manuscript », filtre les résultats par institution, récupère les manifests et renvoie au client une URL d’ouverture dans Mirador.

---

## 6. Fonctionnalités détaillées

## 6.1 Onglet Recherche

Doit contenir :

* champ de recherche plein texte ;
* bouton rechercher ;
* filtres latéraux ;
* sélecteur de sources ;
* mode recherche simple / avancée ;
* affichage galerie ;
* pagination ou scroll infini.

### 6.1.1 Recherche simple

Un seul champ libre interroge plusieurs sources.

### 6.1.2 Recherche avancée

Champs optionnels :

* mots-clés ;
* institution ;
* type de document ;
* langue ;
* date min ;
* date max ;
* disponibilité IIIF ;
* présence d’image ;
* présence d’OCR.

### 6.1.3 Galerie de résultats

Chaque carte doit afficher :

* miniature ;
* titre ;
* institution ;
* type d’objet ;
* date ;
* auteur / créateur si disponible ;
* indicateur IIIF ;
* indicateur OCR ;
* lien notice ;
* bouton « Ouvrir dans Mirador » ;
* case à cocher « comparer ».

## 6.2 Onglet Lecture

Cet onglet embarque Mirador.

Fonctions attendues :

* ouverture d’un manifest ;
* ouverture de plusieurs manifests ;
* disposition multi-fenêtres ;
* zoom, rotation, navigation canvas/page ;
* panneau métadonnées ;
* bouton partage d’URL ;
* bouton retour résultats.

## 6.3 Barre d’actions rapides

Visible depuis les cartes de résultats :

* ouvrir ;
* ajouter à la comparaison ;
* copier manifest ;
* copier notice ;
* ouvrir dans un nouvel onglet.

## 6.4 Import manuel

Une interface doit permettre :

* de coller une URL de manifest ;
* de coller une URL de notice ;
* de saisir un identifiant connu selon certaines sources.

Le backend tente alors :

1. de reconnaître la source ;
2. de récupérer le manifest ;
3. de charger Mirador.

## 6.5 Journal de transparence

Pour chaque résultat, un panneau optionnel « Voir la provenance » doit pouvoir afficher :

* connecteur utilisé ;
* requête envoyée ;
* temps de réponse ;
* niveau de confiance de normalisation ;
* champs absents.

---

## 7. Architecture globale

## 7.1 Vue d’ensemble

Le système comporte :

### Frontend

* application React ou Next.js ;
* interface utilisateur ;
* intégration Mirador ;
* gestion de l’état ;
* appel à l’API backend.

### Backend

* FastAPI ;
* orchestrateur de recherche ;
* normalisation des métadonnées ;
* cache ;
* résolution de manifests ;
* endpoints REST ;
* couche MCP optionnelle.

### Déploiement

* Hugging Face Space Docker ;
* variables d’environnement ;
* stockage léger pour cache local ;
* logs standardisés.

---

## 8. Choix techniques recommandés

## 8.1 Frontend

* React + TypeScript
* Vite ou Next.js
* TanStack Query pour les appels réseau
* Zustand ou Redux Toolkit pour l’état global
* composant Mirador intégré dans une vue dédiée
* Tailwind CSS pour l’UI

## 8.2 Backend

* Python 3.11+
* FastAPI
* httpx pour appels asynchrones
* pydantic pour modèles
* cachetools ou redis optionnel si disponible
* structlog ou logging JSON

## 8.3 MCP

* couche séparée, facultative au démarrage
* outils exposés par-dessus les mêmes services métiers que le REST
* surtout aucune logique dupliquée entre REST et MCP

## 8.4 Déploiement

* conteneur unique au MVP
* frontend servi soit statiquement, soit via le backend
* config simple via variables d’environnement

---

## 9. Architecture logique détaillée

## 9.1 Modules backend

### a. Search Orchestrator

Responsabilités :

* recevoir une requête utilisateur ;
* sélectionner les connecteurs à appeler ;
* lancer les appels en parallèle ;
* agréger les réponses ;
* normaliser les résultats ;
* classer ;
* renvoyer la réponse unifiée.

### b. Connector Registry

Registre de tous les connecteurs disponibles.

Fonctions :

* lister les connecteurs ;
* indiquer leurs capacités ;
* savoir lesquels sont activés ;
* fournir l’instance du connecteur demandé.

### c. Source Connectors

Un connecteur par source.

Interface commune obligatoire :

* `search(query, filters, page, page_size)`
* `get_item(source_id)`
* `resolve_manifest(item_or_url)`
* `healthcheck()`
* `capabilities()`

### d. Normalization Layer

Transforme des réponses hétérogènes en schéma commun.

### e. Manifest Resolver

Essaye de trouver un manifest à partir de :

* métadonnées de résultat ;
* URL de notice ;
* endpoint spécifique de la source ;
* heuristiques configurées.

### f. Cache Layer

Cache des requêtes de recherche et des résolutions de manifest.

### g. MCP Adapter

Expose certains services backend sous forme d’outils MCP.

---

## 10. Contrat des connecteurs

Chaque connecteur doit implémenter une classe abstraite commune.

### 10.1 Interface conceptuelle

```python
class BaseConnector(ABC):
    name: str
    source_type: str

    @abstractmethod
    async def search(self, query: str, filters: dict, page: int, page_size: int) -> SearchResultPage:
        ...

    @abstractmethod
    async def get_item(self, source_id: str) -> NormalizedItem | None:
        ...

    @abstractmethod
    async def resolve_manifest(self, item: NormalizedItem | None = None, url: str | None = None) -> str | None:
        ...

    @abstractmethod
    async def capabilities(self) -> dict:
        ...

    @abstractmethod
    async def healthcheck(self) -> dict:
        ...
```

### 10.2 Capacités déclaratives

Un connecteur doit déclarer explicitement :

* recherche libre oui/non ;
* recherche structurée oui/non ;
* pagination oui/non ;
* facettes oui/non ;
* résolution manifest directe oui/non ;
* OCR signalé oui/non ;
* miniature disponible oui/non.

---

## 11. Schéma de données normalisé

## 11.1 Objet principal : NormalizedItem

```json
{
  "id": "global-unique-id",
  "source": "gallica",
  "source_label": "Gallica / BnF",
  "source_item_id": "ark-or-internal-id",
  "title": "string",
  "subtitle": "string|null",
  "creators": ["string"],
  "date_display": "string|null",
  "date_sort": "string|null",
  "languages": ["string"],
  "object_type": "manuscript|book|image|map|newspaper|other",
  "description": "string|null",
  "thumbnail_url": "string|null",
  "preview_image_url": "string|null",
  "institution": "string|null",
  "collection": "string|null",
  "rights": "string|null",
  "license": "string|null",
  "record_url": "string|null",
  "manifest_url": "string|null",
  "iiif_image_service_url": "string|null",
  "has_iiif_manifest": true,
  "has_images": true,
  "has_ocr": false,
  "availability": "public|restricted|unknown",
  "relevance_score": 0.0,
  "raw_source_payload": {},
  "normalization_warnings": ["string"]
}
```

## 11.2 Réponse de recherche

```json
{
  "query": "book of hours",
  "page": 1,
  "page_size": 24,
  "total_estimated": 214,
  "results": [],
  "sources_used": ["gallica", "bodleian", "europeana"],
  "partial_failures": [
    {
      "source": "bodleian",
      "error": null,
      "status": "ok"
    }
  ],
  "duration_ms": 942,
  "facets": {
    "source": [],
    "object_type": [],
    "language": []
  }
}
```

---

## 12. API REST interne

## 12.1 Endpoints principaux

### `GET /api/health`

Retourne l’état global de l’application.

### `GET /api/sources`

Retourne la liste des connecteurs actifs et leurs capacités.

### `POST /api/search`

Entrée :

```json
{
  "query": "book of hours",
  "sources": ["gallica", "bodleian"],
  "filters": {
    "object_type": ["manuscript"],
    "language": ["lat"],
    "has_iiif_manifest": true
  },
  "page": 1,
  "page_size": 24,
  "sort": "relevance"
}
```

Sortie : SearchResponse normalisée.

### `GET /api/item/{global_id}`

Retourne le détail d’un item normalisé.

### `POST /api/resolve-manifest`

Entrée :

```json
{
  "source": "gallica",
  "source_item_id": "identifier",
  "record_url": "optional"
}
```

Sortie :

```json
{
  "manifest_url": "https://.../manifest",
  "status": "resolved",
  "method": "metadata|heuristic|source-api"
}
```

### `POST /api/open`

Entrée :

```json
{
  "manifest_urls": ["https://example.org/manifest/1"],
  "workspace": "default"
}
```

Sortie :

```json
{
  "mirador_state": {}
}
```

### `POST /api/import`

Permet d’importer une URL libre.

Entrée :

```json
{
  "url": "https://example.org/item/or/manifest"
}
```

Sortie :

```json
{
  "detected_source": "bodleian",
  "record_url": "...",
  "manifest_url": "...",
  "item": {}
}
```

---

## 13. Outils MCP à exposer

Le serveur MCP doit réutiliser les mêmes services métiers que l’API REST.

### Outils minimum

#### `search_items`

Paramètres :

* query
* sources
* filters
* page
* page_size

Retour : liste normalisée de résultats.

#### `get_item`

Paramètres :

* global_id

Retour : détail d’un item.

#### `resolve_manifest`

Paramètres :

* global_id ou URL

Retour : manifest URL.

#### `open_in_mirador`

Paramètres :

* une ou plusieurs manifest URLs

Retour : URL d’ouverture ou état Mirador sérialisé.

#### `list_sources`

Retour : sources actives et capacités.

### Ressources MCP éventuelles

* catalogue des sources
* documentation des schémas
* exemples de requêtes

---

## 14. Intégration Mirador

## 14.1 Attentes fonctionnelles

Mirador doit être embarqué comme composant de lecture.

L’application doit pouvoir :

* initialiser Mirador avec zéro, une ou plusieurs fenêtres ;
* injecter dynamiquement les manifests sélectionnés ;
* mémoriser l’état courant de la session ;
* permettre un partage d’URL si possible.

## 14.2 Mode d’intégration

Créer un composant `MiradorWorkspace` qui reçoit une liste de manifests et une configuration.

Exemple de props :

```ts
interface MiradorWorkspaceProps {
  manifestUrls: string[]
  initialView?: "single" | "compare"
  showMetadata?: boolean
  onStateChange?: (state: unknown) => void
}
```

## 14.3 État applicatif

Le frontend doit stocker séparément :

* résultats de recherche ;
* sélection pour comparaison ;
* manifests ouverts ;
* configuration du workspace.

---

## 15. UI et UX détaillées

## 15.1 Navigation principale

* onglet Recherche
* onglet Lecture
* onglet Import
* onglet Sources
* onglet À propos

## 15.2 Page Recherche

### Colonne gauche

* sources
* type d’objet
* période
* langue
* disponibilité IIIF
* présence OCR

### Zone centrale

* barre de recherche
* tri
* nombre de résultats
* cartes résultats

### Colonne droite optionnelle

* panier de comparaison
* aperçu rapide du résultat sélectionné

## 15.3 Cartes résultats

Doivent être lisibles, homogènes et sobres.

Actions visibles :

* ouvrir
* comparer
* détails

## 15.4 Page Lecture

* bandeau avec titres des objets ouverts
* zone Mirador principale
* panneau latéral avec métadonnées et provenance

## 15.5 Page Sources

Affiche pour chaque source :

* nom
* description
* statut
* capacités
* notes spécifiques
* exemple de requête test

---

## 16. Classement et fusion des résultats

Le système doit agréger des résultats hétérogènes. Il faut donc définir une stratégie de ranking simple au MVP.

### 16.1 Score de base

Combiner :

* score natif de la source si disponible ;
* qualité de correspondance textuelle locale ;
* disponibilité d’un manifest ;
* présence d’une miniature ;
* complétude des métadonnées.

### 16.2 Déduplication légère

Tenter de détecter des doublons faibles via :

* titre normalisé ;
* identifiants communs ;
* URLs canoniques ;
* manifest identique.

En cas de doute, ne pas fusionner automatiquement au MVP.

---

## 17. Performance et robustesse

## 17.1 Appels concurrents

Le backend doit appeler les connecteurs en parallèle avec timeout par source.

## 17.2 Timeouts

Chaque source doit avoir :

* timeout connexion ;
* timeout lecture ;
* timeout global par requête.

## 17.3 Partial success

Si une source échoue, les autres résultats doivent quand même apparaître.

## 17.4 Cache

Mettre en cache :

* résultats de recherche récents ;
* résolutions de manifest ;
* capacités des sources.

## 17.5 Limitation

Ajouter un plafond raisonnable de sources interrogées simultanément au MVP.

---

## 18. Sécurité et conformité

## 18.1 Sécurité minimale

* validation stricte des URLs importées ;
* blocage des schémas non autorisés ;
* prévention SSRF basique ;
* limitation des domaines si nécessaire ;
* logs sans données sensibles.

## 18.2 Respect des sources

* afficher la source d’origine ;
* ne pas masquer les droits ;
* ne pas revendiquer la propriété des données ;
* lien systématique vers la notice d’origine.

## 18.3 CORS et proxy

Prévoir un backend pouvant agir comme intermédiaire pour certains appels si le frontend rencontre des restrictions cross-origin.

---

## 19. Observabilité

Prévoir :

* logs structurés ;
* mesure des temps par source ;
* taux de résolution des manifests ;
* taux d’échec par connecteur ;
* nombre moyen de résultats par source.

---

## 20. Arborescence de projet recommandée

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

---

## 21. Plan de développement par étapes

## Phase 1 — socle

* boot frontend ;
* boot backend ;
* endpoint health ;
* intégration Mirador minimale ;
* schéma `NormalizedItem`.

## Phase 2 — connecteurs MVP

* connecteur Gallica ;
* connecteur Bodleian ;
* connecteur Europeana ;
* registre de connecteurs ;
* orchestration de recherche.

## Phase 3 — UX recherche

* galerie ;
* filtres ;
* pagination ;
* détail item ;
* ouverture Mirador.

## Phase 4 — import et résolution

* import URL ;
* résolution manifest ;
* comparaison multi-fenêtres.

## Phase 5 — MCP

* outils minimum ;
* documentation ;
* exemples clients.

## Phase 6 — polissage

* cache ;
* logs ;
* robustesse ;
* amélioration ranking.

---

## 22. Critères d’acceptation du MVP

Le MVP est considéré comme acceptable si :

1. une requête simple renvoie des résultats depuis au moins trois sources ;
2. les résultats sont affichés dans une galerie homogène ;
3. au moins 80 % des résultats disposant réellement d’un manifest peuvent être ouverts dans Mirador ;
4. l’ouverture de plusieurs objets dans Mirador fonctionne ;
5. l’échec d’une source n’empêche pas la réponse globale ;
6. l’API `/api/sources` décrit clairement les capacités ;
7. l’import d’une URL de manifest fonctionne ;
8. les fonctions principales sont exposées aussi via MCP si la couche MCP est activée.

---

## 23. Non-objectifs explicites

Le document doit clairement indiquer ce que le produit n’est pas :

* ce n’est pas un moteur de recherche web généraliste ;
* ce n’est pas un catalogue mondial exhaustif ;
* ce n’est pas une base propriétaire remplaçant les institutions ;
* ce n’est pas un viewer maison destiné à remplacer Mirador ;
* ce n’est pas une solution d’annotation scientifique complète au MVP.

---

## 24. Spécification pour génération de code par LLM

Le LLM chargé de coder le projet doit respecter les consignes suivantes.

### 24.1 Contraintes générales

* tout le code doit être typé ;
* tout le code doit être modulaire ;
* aucune logique métier dupliquée entre REST et MCP ;
* chaque connecteur doit être isolé ;
* chaque fonction publique doit avoir docstring ou commentaire clair ;
* les erreurs doivent être gérées proprement ;
* les appels réseau doivent être asynchrones côté backend.

### 24.2 Contraintes frontend

* TypeScript strict ;
* composants réutilisables ;
* éviter les dépendances inutiles ;
* UI simple et claire ;
* aucun style inline massif ;
* préférer Tailwind.

### 24.3 Contraintes backend

* FastAPI ;
* modèles Pydantic ;
* services séparés des routes ;
* tests unitaires des connecteurs ;
* tests d’intégration des endpoints.

### 24.4 Livrables attendus du LLM

* code complet frontend ;
* code complet backend ;
* Dockerfile ;
* README d’installation ;
* exemples `.env.example` ;
* tests minimum ;
* documentation d’API.

---

## 25. Prompt maître pour un LLM codeur

```text
Tu dois générer un projet complet déployable sur Hugging Face Spaces sous forme d’application web Docker.

Objectif du produit : une interface de recherche fédérée sur plusieurs sources patrimoniales, avec affichage d’une galerie de résultats normalisés, puis ouverture directe des objets dans Mirador à partir de leurs manifests IIIF.

Contraintes :
- frontend React + TypeScript ;
- backend FastAPI Python ;
- architecture modulaire ;
- connecteurs par source ;
- schéma de données normalisé ;
- Mirador intégré comme couche de lecture ;
- API REST interne ;
- couche MCP optionnelle mais prévue ;
- code propre, typé, documenté, testable.

Fonctionnalités MVP :
- champ de recherche ;
- sélection de sources ;
- filtres simples ;
- galerie de résultats ;
- bouton ouvrir dans Mirador ;
- comparaison multi-objets ;
- import manuel d’URL de manifest ;
- endpoint listant les sources et capacités.

Architecture attendue :
- dossier frontend ;
- dossier backend ;
- dossier tests ;
- Dockerfile ;
- README.

Backend :
- créer une interface abstraite BaseConnector ;
- implémenter un registry de connecteurs ;
- implémenter un orchestrateur de recherche ;
- définir les modèles Pydantic NormalizedItem, SearchResponse, SourceCapability ;
- créer les endpoints /api/health, /api/sources, /api/search, /api/item/{id}, /api/resolve-manifest, /api/import.

Frontend :
- créer une page Recherche ;
- créer une page Lecture avec Mirador ;
- créer un store pour la sélection des résultats ;
- créer des cartes de résultats ;
- permettre d’ouvrir un ou plusieurs manifests dans Mirador.

Important :
- ne pas coder de logique de recherche dans Mirador ;
- séparer nettement découverte et lecture ;
- gérer les erreurs partielles des sources ;
- prévoir des mocks si certaines API réelles sont instables.

Commence par générer l’arborescence complète du projet, puis le backend, puis le frontend, puis les tests, puis le Dockerfile et le README.
```

---

## 26. Prompts spécialisés par lot

## Prompt lot 1 — backend socle

```text
Génère uniquement le backend FastAPI du projet.

Exigences :
- Python 3.11+
- FastAPI
- Pydantic
- httpx async
- architecture modulaire
- BaseConnector abstraite
- ConnectorRegistry
- SearchOrchestrator
- modèles NormalizedItem, SearchResponse, SourceInfo
- endpoints : /api/health, /api/sources, /api/search, /api/item/{id}, /api/resolve-manifest, /api/import
- gestion d’erreurs propre
- docstrings
- tests unitaires de base

Ne génère pas encore le frontend.
```

## Prompt lot 2 — frontend socle

```text
Génère uniquement le frontend React + TypeScript du projet.

Exigences :
- page Recherche
- filtres latéraux
- galerie de résultats
- composant ResultCard
- store global pour manifests sélectionnés
- page Lecture intégrant Mirador
- navigation simple entre Recherche et Lecture
- Tailwind CSS
- code propre et typé

Le frontend doit appeler les endpoints du backend déjà définis.
```

## Prompt lot 3 — connecteurs

```text
Ajoute au backend un système de connecteurs source.

Exigences :
- implémenter BaseConnector
- créer au moins 3 connecteurs d’exemple
- chaque connecteur doit renvoyer des résultats normalisés
- prévoir un mode mock si la source distante n’est pas disponible
- ne pas dupliquer la logique de normalisation
```

## Prompt lot 4 — MCP

```text
Ajoute une couche MCP au backend existant.

Exigences :
- exposer les outils search_items, get_item, resolve_manifest, open_in_mirador, list_sources
- réutiliser les mêmes services métiers que les routes REST
- ne créer aucune duplication de logique
- fournir un exemple minimal d’utilisation par un client MCP
```

---

## 27. Backlog post-MVP

Après le MVP, prévoir :

* sauvegarde de sessions ;
* favoris ;
* export CSV / JSON des résultats ;
* partage de workspace Mirador ;
* annotation persistante ;
* index local optionnel ;
* détection de doublons plus avancée ;
* recherche intra-document via Content Search IIIF quand disponible ;
* enrichissement sémantique ;
* facettes avancées ;
* recommandation d’objets similaires.

---

## 28. Décisions produit à ne pas perdre

1. Mirador est la couche de lecture, jamais la couche de recherche.
2. Les connecteurs sont les unités fondamentales d’extension.
3. Le schéma normalisé est le cœur du projet.
4. Le MVP privilégie la simplicité et la robustesse sur l’exhaustivité.
5. Le MCP est utile comme surcouche d’interopérabilité, pas comme justification unique du produit.

---

## 29. Version courte à remettre à un développeur ou à un LLM

Créer une application web déployable sur Hugging Face Spaces qui permet de rechercher des objets patrimoniaux dans plusieurs institutions, d’afficher les résultats sous forme de galerie homogène, puis d’ouvrir directement les objets dans Mirador à partir de leurs manifests IIIF.

Le produit comprend :

* un frontend React/TypeScript ;
* un backend FastAPI ;
* des connecteurs source modulaires ;
* un schéma de données normalisé ;
* Mirador intégré ;
* une API REST ;
* une couche MCP optionnelle.

Le MVP doit inclure recherche fédérée, filtres simples, galerie, ouverture Mirador, comparaison multi-objets et import manuel d’URL de manifest.

Le système doit être robuste aux échecs partiels, simple à étendre et proprement documenté.
