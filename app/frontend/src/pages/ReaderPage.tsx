import { Link } from 'react-router-dom'

import { MiradorWorkspace } from '../lib/mirador/MiradorWorkspace'
import { useReaderStore } from '../store/readerStore'
import { useSearchStore } from '../store/searchStore'

export function ReaderPage() {
  const openManifestUrls = useReaderStore((state) => state.openManifestUrls)
  const viewMode = useReaderStore((state) => state.readerConfig.viewMode)
  const showMetadata = useReaderStore((state) => state.readerConfig.showMetadata)
  const setViewMode = useReaderStore((state) => state.setViewMode)
  const setShowMetadata = useReaderStore((state) => state.setShowMetadata)

  const selectedForComparison = useSearchStore((state) => state.selectedForComparison)
  const results = useSearchStore((state) => state.results)

  const selectedManifestUrls = results
    .filter((item) => selectedForComparison.includes(item.id) && item.manifest_url)
    .map((item) => item.manifest_url as string)

  const manifestUrls = viewMode === 'compare' ? selectedManifestUrls : openManifestUrls

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-lg font-semibold">Lecture</h1>
        <Link className="rounded border border-slate-300 px-3 py-1 text-sm" to="/search">
          Retour vers Recherche
        </Link>
      </div>

      <p className="text-sm text-slate-600">Mirador est utilisé ici uniquement comme workspace de lecture.</p>

      <div className="flex flex-wrap items-center gap-3 rounded-md border border-slate-200 bg-white p-3 text-sm">
        <label className="flex items-center gap-2">
          <input
            checked={viewMode === 'single'}
            type="radio"
            name="viewMode"
            onChange={() => setViewMode('single')}
          />
          Vue simple ({openManifestUrls.length})
        </label>
        <label className="flex items-center gap-2">
          <input
            checked={viewMode === 'compare'}
            type="radio"
            name="viewMode"
            onChange={() => setViewMode('compare')}
          />
          Vue comparaison ({selectedManifestUrls.length})
        </label>
        <label className="flex items-center gap-2">
          <input
            checked={showMetadata}
            type="checkbox"
            onChange={(event) => setShowMetadata(event.target.checked)}
          />
          Afficher les métadonnées
        </label>
      </div>

      <MiradorWorkspace
        manifestUrls={manifestUrls}
        initialView={viewMode}
        showMetadata={showMetadata}
        onStateChange={() => {
          // Lot 3: hook kept minimal for future share/persistence extensions.
        }}
      />
    </section>
  )
}
