# AGENTS.md

## Mission du dépôt

Construire une application web déployable sur Hugging Face Spaces permettant :

1. de rechercher des objets patrimoniaux dans plusieurs institutions ;
2. de normaliser les résultats dans un schéma commun ;
3. d’ouvrir directement les ressources dans Mirador à partir de manifests IIIF ;
4. d’exposer les fonctions principales via une API REST ;
5. d’exposer éventuellement les mêmes fonctions via MCP, sans duplication de logique métier.

Le produit est structuré en trois couches :

- découverte : recherche fédérée multi-sources ;
- lecture : viewer Mirador ;
- interopérabilité : API REST interne + couche MCP optionnelle.

## Principes produit à ne jamais perdre

1. Mirador est une couche de lecture, jamais une couche de recherche.
2. Les connecteurs sont les unités fondamentales d’extension.
3. Le schéma de données normalisé est le cœur du projet.
4. Le MVP privilégie la robustesse, la simplicité et l’extensibilité.
5. Le système doit tolérer les échecs partiels des sources.
6. Le produit n’est pas un moteur de recherche web généraliste.
7. Le produit n’est pas un catalogue mondial exhaustif.
8. Le produit ne remplace pas les institutions sources : il les relie et les rend plus lisibles.

## Architecture attendue

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

## Technologies cibles

### Frontend

- React
- TypeScript strict
- Vite ou Next.js
- Tailwind CSS
- TanStack Query
- Zustand ou Redux Toolkit
- Mirador intégré comme composant de lecture

### Backend

- Python 3.11+
- FastAPI
- Pydantic
- httpx async
- cache mémoire simple au MVP
- logging structuré

## Règles absolues

### Séparation des responsabilités

- Mirador ne doit contenir aucune logique métier de recherche.
- Les routes REST ne doivent pas contenir de logique métier complexe.
- Les services contiennent la logique métier.
- Les connecteurs encapsulent l’accès aux sources externes.
- MCP doit réutiliser les mêmes services que REST.
- Aucune duplication de logique métier entre REST et MCP.

### Connecteurs

Chaque connecteur doit implémenter une interface commune de type `BaseConnector`.

#### Méthodes minimales

- `search(query, filters, page, page_size)`
- `get_item(source_id)`
- `resolve_manifest(item_or_url)`
- `healthcheck()`
- `capabilities()`

Chaque connecteur doit :

- être isolé dans son propre module ;
- normaliser ses sorties dans le schéma commun ;
- gérer les erreurs proprement ;
- proposer un mode mock si la source distante est indisponible ou instable ;
- ne jamais casser la réponse globale en cas d’échec individuel.

### Schéma normalisé

- Toute donnée issue d’une source externe doit être transformée en `NormalizedItem`.
- Aucune UI ne doit dépendre directement d’un payload brut de source externe.
- Le schéma normalisé est la vérité interne de l’application.

### Réseau et robustesse

- Tous les appels externes backend doivent être asynchrones.
- Chaque source doit être protégée par un timeout raisonnable.
- La recherche fédérée doit supporter les succès partiels.
- Les résolutions de manifest doivent être mises en cache au MVP si simple à faire.
- Les imports d’URL doivent être validés strictement.
- Prévenir les usages dangereux de type SSRF avec allowlist ou validation stricte des domaines/schémas si nécessaire.

### Frontend

- TypeScript strict obligatoire.
- Composants réutilisables.
- Pas de style inline massif.
- Préférer Tailwind.
- Pas d’appel direct à des APIs sources depuis le frontend si cela contourne le backend métier.
- Le store global ne doit contenir que l’état utile partagé.

### Qualité de code

- Tout code doit être typé.
- Toute fonction publique doit avoir une docstring ou un commentaire utile.
- Toute erreur utilisateur ou réseau importante doit être gérée explicitement.
- Les noms de fichiers, fonctions et classes doivent être clairs et stables.
- Préférer un code simple, lisible et modulaire à une sophistication prématurée.

## Contrat du MVP

### Le MVP doit inclure

- recherche fédérée sur 3 à 5 sources maximum ;
- normalisation des résultats ;
- galerie homogène ;
- ouverture d’un item dans Mirador ;
- comparaison de plusieurs manifests dans Mirador ;
- import manuel de manifest ou URL de notice ;
- endpoint listant les sources et leurs capacités ;
- couche MCP optionnelle mais prévue proprement.

### Le MVP ne doit pas inclure

- compte utilisateur ;
- annotation persistante collaborative ;
- moissonnage global du web patrimonial ;
- index mondial complet ;
- recherche OCR universelle sur tout le web patrimonial ;
- fusion agressive ou incertaine de doublons.

## Définition de terminé

Un lot n’est considéré comme terminé que si :

- il respecte le périmètre demandé et ne déborde pas ;
- il compile ou build correctement ;
- les tests du lot passent ;
- les nouveaux fichiers sont rangés dans la bonne architecture ;
- les limites restantes sont clairement documentées ;
- aucune logique métier n’a été dupliquée ;
- le code généré reste cohérent avec `docs/specs.md`.

## Ce qu’il faut vérifier à chaque lot

### Backend

- routes présentes ;
- modèles Pydantic cohérents ;
- services séparés des routes ;
- appels async corrects ;
- gestion des erreurs ;
- succès partiels ;
- tests unitaires minimum ;
- tests d’intégration minimum pour endpoints critiques.

### Frontend

- typecheck OK ;
- build OK ;
- navigation fonctionnelle ;
- composants réutilisables ;
- appels backend conformes au contrat ;
- gestion des états de chargement, vide et erreur.

### Connecteurs

- interface respectée ;
- mode mock disponible si pertinent ;
- mapping vers `NormalizedItem` correct ;
- test unitaire de normalisation ;
- test d’échec partiel.

### MCP

- réutilisation des services existants ;
- aucune duplication ;
- documentation minimale ;
- exemple de client.

## Fichiers de référence à lire avant toute implémentation

Toujours lire :

- `AGENTS.md`
- `docs/specs.md`
- `docs/mvp-scope.md`
- `docs/architecture.md`
- `docs/acceptance-checklist.md`

## Priorités d’implémentation

Ordre recommandé :

1. structure repo + docs ;
2. backend socle ;
3. frontend socle ;
4. Mirador minimal ;
5. import manifest manuel ;
6. connecteurs réels ;
7. ranking simple + cache + observabilité ;
8. MCP ;
9. Docker + déploiement Hugging Face Spaces ;
10. polissage final.

## Comportement attendu de l’agent codeur

Quand une tâche est demandée :

- analyser le périmètre ;
- proposer un mini-plan ;
- implémenter uniquement le lot demandé ;
- écrire ou compléter les tests utiles ;
- exécuter les vérifications pertinentes ;
- résumer ce qui a été fait ;
- lister honnêtement les limites et la suite.

### Ne pas

- élargir arbitrairement le périmètre ;
- réécrire l’architecture sans nécessité ;
- introduire des dépendances inutiles ;
- inventer des contrats API incompatibles avec les specs ;
- mélanger code temporaire et code de production sans l’indiquer.

## Règle spéciale Mirador

Mirador doit être traité comme un workspace de lecture recevant une ou plusieurs URLs de manifest.

### Ne jamais

- implémenter la recherche métier dans Mirador ;
- faire dépendre le moteur fédéré d’API internes Mirador ;
- confondre découverte et lecture.

## Règle spéciale MCP

MCP est une couche d’exposition, pas un second backend.

Les outils MCP doivent réutiliser les mêmes services métiers que REST :

- `search_items`
- `get_item`
- `resolve_manifest`
- `open_in_mirador`
- `list_sources`

## Critère de succès global du MVP

Le MVP est acceptable si :

- une requête simple renvoie des résultats depuis au moins trois sources ;
- les résultats apparaissent dans une galerie homogène ;
- l’ouverture IIIF dans Mirador fonctionne pour la majorité des items ayant un manifest ;
- l’ouverture multi-objets fonctionne ;
- l’échec d’une source n’empêche pas la réponse globale ;
- l’API `/api/sources` décrit clairement les capacités ;
- l’import d’un manifest URL fonctionne ;
- MCP fonctionne si activé, sans logique dupliquée.
