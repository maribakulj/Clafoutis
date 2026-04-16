import { useSources } from '../hooks/useSources'

export function SourcesPage() {
  const sources = useSources()

  if (sources.isPending) {
    return <p className="text-sm text-slate-600" role="status">Chargement des sources...</p>
  }

  if (sources.isError) {
    return (
      <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700" role="alert">
        Erreur: {sources.error.message}
      </p>
    )
  }

  return (
    <section className="space-y-4">
      <h1 className="text-lg font-semibold">Sources</h1>
      <div className="grid gap-3" role="list" aria-label="Liste des sources">
        {sources.data.sources.map((source) => (
          <article
            key={source.name}
            role="listitem"
            className="rounded-md border border-slate-200 bg-white p-4 text-sm"
            aria-label={source.label}
          >
            <p className="font-semibold">{source.label}</p>
            <dl className="mt-1 space-y-0.5 text-slate-600">
              <div className="flex gap-1">
                <dt>Nom:</dt>
                <dd>{source.name}</dd>
              </div>
              <div className="flex gap-1">
                <dt>Type:</dt>
                <dd>{source.source_type}</dd>
              </div>
              <div className="flex gap-1">
                <dt>Statut:</dt>
                <dd>{source.healthy ? 'ok' : 'error'}</dd>
              </div>
            </dl>
          </article>
        ))}
      </div>
    </section>
  )
}
