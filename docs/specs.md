# Spécification produit et technique (référence docs)

Ce fichier reprend la spécification de référence du dépôt afin de centraliser la documentation sous `docs/`.

La source canonique actuellement maintenue dans le repo est `specs.md` à la racine.

## Référence

- Voir le document complet : [`../specs.md`](../specs.md)

## Résumé opérationnel

Le produit est structuré en 3 couches :

1. **Découverte** : recherche fédérée multi-sources.
2. **Lecture** : visualisation IIIF dans Mirador.
3. **Interopérabilité** : API REST interne + couche MCP optionnelle.

Contraintes majeures :

- Mirador est une couche de lecture uniquement.
- Les connecteurs sont les unités d’extension.
- Toute donnée externe doit être normalisée (`NormalizedItem`).
- Le système doit tolérer les échecs partiels.
- Le MVP cible 3 à 5 sources.
