# PLANS.md

## But

Ce document découpe le développement en lots courts, testables et adaptés à un workflow avec Codex.

Chaque lot doit pouvoir être traité dans une branche ou worktree séparé.

---

## Vue d’ensemble

Ordre recommandé :

1. Lot 0 — cadrage repo
2. Lot 1 — backend socle
3. Lot 2 — frontend socle
4. Lot 3 — intégration Mirador minimale
5. Lot 4 — import manuel + manifest-by-url
6. Lot 5 — connecteur Gallica
7. Lot 6 — connecteurs Bodleian + Europeana
8. Lot 7 — ranking, cache, partial failures, provenance
9. Lot 8 — couche MCP
10. Lot 9 — Docker + Hugging Face Spaces
11. Lot 10 — hardening final

---

## Lot 0 — cadrage repo

### Objectif
Poser la structure de travail, les conventions et la documentation de référence.

### Livrables
- `AGENTS.md`
- `docs/specs.md`
- `docs/mvp-scope.md`
- `docs/architecture.md`
- `docs/acceptance-checklist.md`
- `README.md` minimal
- arborescence vide du monorepo

### Critères de validation
- l’arborescence cible est claire ;
- les conventions sont écrites ;
- les lots suivants peuvent être lancés sans ambiguïté.

---

## Lot 1 — backend socle

### Objectif
Créer le noyau backend stable avant les connecteurs réels.

### Inclus
- FastAPI bootable
- config minimale
- modèles Pydantic
- `BaseConnector`
- `ConnectorRegistry`
- `SearchOrchestrator`
- endpoints :
  - `/api/health`
  - `/api/sources`
  - `/api/search`
  - `/api/item/{id}`
  - `/api/resolve-manifest`
  - `/api/import`
- connecteur mock de démonstration
- tests unitaires et intégration de base

### Exclu
- vrais connecteurs complexes
- logique MCP
- cache avancé

### Critères de validation
- l’API démarre ;
- les modèles sont stables ;
- les routes répondent ;
- les succès partiels sont prévus ;
- le frontend peut déjà se brancher dessus.

---

## Lot 2 — frontend socle

### Objectif
Mettre en place l’interface de base branchée sur le backend socle.

### Inclus
- React + TypeScript
- Tailwind
- navigation principale :
  - Recherche
  - Lecture
  - Import
  - Sources
  - À propos
- store global
- barre de recherche
- filtres basiques
- galerie de résultats
- composant `ResultCard`
- gestion loading / empty / error
- page Sources
- branchement API backend

### Exclu
- connecteurs réels complexes
- ranking avancé
- features post-MVP

### Critères de validation
- le frontend build ;
- une recherche mock affiche des cartes ;
- la navigation est stable ;
- l’ouverture vers Lecture est préparée.

---

## Lot 3 — intégration Mirador minimale

### Objectif
Intégrer Mirador proprement comme viewer de lecture.

### Inclus
- composant `MiradorWorkspace`
- ouverture d’un manifest
- ouverture de plusieurs manifests
- mode simple / compare
- stockage léger des manifests ouverts
- lien entre résultats sélectionnés et page Lecture

### Exclu
- logique de recherche dans Mirador
- persistance avancée de session

### Critères de validation
- un manifest URL peut être ouvert ;
- plusieurs manifests peuvent être affichés ;
- la sélection depuis la galerie alimente bien Mirador.

---

## Lot 4 — import manuel + connecteur manifest-by-url

### Objectif
Créer le chemin le plus robuste de démonstration fonctionnelle.

### Inclus
- page Import
- validation d’URL
- détection manifest direct
- heuristiques simples de notice -> manifest
- connecteur `manifest_by_url`
- tests de sécurité basiques
- tests d’import

### Critères de validation
- coller une URL de manifest ouvre Mirador ;
- l’API `/api/import` fonctionne ;
- les URLs invalides sont rejetées proprement.

---

## Lot 5 — connecteur Gallica

### Objectif
Ajouter la première source réelle prioritaire.

### Inclus
- connecteur Gallica
- mapping vers `NormalizedItem`
- recherche simple
- `get_item`
- `resolve_manifest`
- mode mock ou fixtures
- tests unitaires du mapping
- tests d’intégration ciblés

### Critères de validation
- une requête simple renvoie des résultats Gallica normalisés ;
- les manifests Gallica sont résolus quand disponible ;
- l’échec Gallica n’empêche pas la réponse globale.

---

## Lot 6 — connecteurs Bodleian + Europeana

### Objectif
Porter la fédération à trois sources réelles minimum.

### Inclus
- connecteur Bodleian
- connecteur Europeana
- normalisation cohérente
- capacités déclaratives
- modes mock ou fixtures
- tests unitaires par connecteur

### Critères de validation
- au moins trois sources fonctionnent ;
- `/api/sources` reflète correctement les capacités ;
- la galerie fusionne les résultats sans casser l’UI.

---

## Lot 7 — ranking, cache, partial failures, provenance

### Objectif
Améliorer la robustesse et la lisibilité des résultats.

### Inclus
- score simple agrégé
- déduplication légère non agressive
- cache mémoire
- journal de provenance
- temps de réponse par source
- `partial_failures`
- timeouts configurables

### Critères de validation
- les temps de réponse sont mieux maîtrisés ;
- les erreurs sont visibles mais non bloquantes ;
- les résultats sont mieux ordonnés ;
- la provenance est consultable.

---

## Lot 8 — MCP

### Objectif
Exposer les fonctions métier via MCP sans créer de deuxième backend.

### Inclus
- outils :
  - `search_items`
  - `get_item`
  - `resolve_manifest`
  - `open_in_mirador`
  - `list_sources`
- documentation minimale
- exemple client
- tests de non-régression si simple

### Exclu
- logique métier dupliquée
- nouveaux modèles indépendants de REST

### Critères de validation
- MCP appelle les mêmes services que REST ;
- les réponses sont cohérentes ;
- aucun fork de logique n’apparaît.

---

## Lot 9 — Docker + Hugging Face Spaces

### Objectif
Rendre le projet réellement déployable.

### Inclus
- Dockerfile
- `.env.example`
- config dev/prod
- scripts de démarrage
- instructions Hugging Face Spaces
- healthcheck de conteneur

### Critères de validation
- build Docker OK ;
- démarrage local OK ;
- documentation de déploiement claire.

---

## Lot 10 — hardening final

### Objectif
Nettoyer et stabiliser avant démonstration.

### Inclus
- revue architecture
- nettoyage dépendances
- vérification typage
- vérification tests
- audit SSRF/import
- polissage UX minimal
- README final
- checklist MVP finale

### Critères de validation
- le MVP est démontrable ;
- la doc est lisible ;
- la structure est propre ;
- les limites connues sont documentées.

---

## Stratégie Git recommandée

### Branches ou worktrees
- `feat/repo-scaffold`
- `feat/backend-core`
- `feat/frontend-shell`
- `feat/mirador`
- `feat/import-manifest`
- `feat/connector-gallica`
- `feat/connectors-bodleian-europeana`
- `feat/ranking-cache-observability`
- `feat/mcp`
- `feat/deploy-hf`
- `chore/hardening`

### Règle
Un lot majeur = une branche ou un worktree.

Ne pas mélanger :
- frontend shell et connecteurs réels dans la même branche ;
- MCP et refonte backend dans la même branche ;
- déploiement et refactoring profond dans la même branche.

---

## Definition of done par lot

Avant merge, vérifier :
- code compilable ;
- tests pertinents passants ;
- docs mises à jour ;
- pas de duplication ;
- pas de débordement de périmètre ;
- limites restantes listées noir sur blanc.
