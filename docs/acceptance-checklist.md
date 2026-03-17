# Acceptance Checklist

## Backend

- [ ] Routes API critiques présentes (`/api/health`, `/api/sources`, `/api/search`, `/api/item/{id}`, `/api/resolve-manifest`, `/api/import`).
- [ ] Modèles Pydantic cohérents et typés.
- [ ] Services séparés des routes.
- [ ] Appels async corrects pour les accès externes.
- [ ] Gestion explicite des erreurs utilisateur/réseau.
- [ ] Support des succès partiels inter-sources.
- [ ] Tests unitaires minimum présents.
- [ ] Tests d’intégration endpoints critiques présents.

## Frontend

- [ ] TypeScript strict activé.
- [ ] Build OK.
- [ ] Navigation fonctionnelle.
- [ ] Composants réutilisables.
- [ ] Appels backend conformes au contrat.
- [ ] États loading/empty/error gérés.

## Connecteurs

- [ ] Interface `BaseConnector` respectée.
- [ ] Mapping vers `NormalizedItem` validé.
- [ ] Mode fixture/mock disponible selon besoin.
- [ ] Test unitaire de normalisation.
- [ ] Test d’échec partiel.

## Lecture / Mirador

- [ ] Aucun code de recherche métier dans Mirador.
- [ ] Ouverture d’un manifest fonctionne.
- [ ] Ouverture de plusieurs manifests fonctionne.

## Déploiement

- [ ] Image Docker buildable.
- [ ] Healthcheck applicatif OK.
- [ ] Workflow HF Space valide.

## Documentation

- [ ] `docs/specs.md` présent.
- [ ] `docs/mvp-scope.md` présent.
- [ ] `docs/architecture.md` présent.
- [ ] `docs/acceptance-checklist.md` présent.
- [ ] Limites connues documentées.
