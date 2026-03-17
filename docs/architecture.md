# Architecture

## Arborescence cible

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

## Principes de séparation

- **API routes** : orchestration HTTP légère.
- **Services** : logique métier.
- **Connecteurs** : encapsulation d’accès aux sources externes.
- **Models** : contrats de données normalisés.
- **Frontend** : pas d’accès direct aux APIs externes institutionnelles.

## Contrat connecteur (`BaseConnector`)

- `search(query, filters, page, page_size)`
- `get_item(source_id)`
- `resolve_manifest(item_or_url)`
- `healthcheck()`
- `capabilities()`

## Robustesse réseau (MVP)

- Appels externes backend asynchrones.
- Timeouts raisonnables.
- Dégradation élégante et succès partiels.
- Validation URL d’import + garde-fous SSRF basiques.
