import { useSources } from '../hooks/useSources'

export function SourcesPage() {
  const sources = useSources()

  if (sources.isPending) {
    return <p className="text-sm text-slate-600">Chargement des sources…</p>
  }

  if (sources.isError) {
    return (
      <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">
        Erreur: {sources.error.message}
      </p>
    )
  }

  return (
    <section className="space-y-4">
      <h1 className="text-lg font-semibold">Sources</h1>
      <div className="grid gap-3">
        {sources.data.sources.map((source) => (
          <article key={source.name} className="rounded-md border border-slate-200 bg-white p-4 text-sm">
            <p className="font-semibold">{source.label}</p>
            <p className="text-slate-600">Nom: {source.name}</p>
            <p className="text-slate-600">Type: {source.source_type}</p>
            <p className="text-slate-600">Statut: {source.healthy ? 'ok' : 'error'}</p>
            <p className="text-slate-600">
              Capacités: search={String(source.capabilities.search)}, get_item=
              {String(source.capabilities.get_item)}, resolve_manifest=
              {String(source.capabilities.resolve_manifest)}
            </p>
          </article>
        ))}
      </div>
    </section>
  )
}
