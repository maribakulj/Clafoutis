import { useCallback } from 'react'

import { SearchBar } from '../components/search/SearchBar'
import { SearchFilters } from '../components/search/SearchFilters'
import { ResultsGrid } from '../components/search/ResultsGrid'
import { useSearch } from '../hooks/useSearch'
import { useReaderStore } from '../store/readerStore'
import { useSearchStore } from '../store/searchStore'
import type { SearchRequest } from '../types/api'
import type { NormalizedItem } from '../types/normalized'

export function SearchPage() {
  const query = useSearchStore((state) => state.query)
  const filters = useSearchStore((state) => state.filters)
  const results = useSearchStore((state) => state.results)
  const selectedForComparison = useSearchStore((state) => state.selectedForComparison)
  const setQuery = useSearchStore((state) => state.setQuery)
  const setFilters = useSearchStore((state) => state.setFilters)
  const toggleCompareSelection = useSearchStore((state) => state.toggleCompareSelection)

  const setOpenManifestUrls = useReaderStore((state) => state.setOpenManifestUrls)
  const setViewMode = useReaderStore((state) => state.setViewMode)

  const search = useSearch()

  const triggerSearch = useCallback(
    (newQuery: string) => {
      if (!newQuery) {
        return
      }
      setQuery(newQuery)
      const payload: SearchRequest = {
        query: newQuery,
        sources: filters.sources.length > 0 ? filters.sources : undefined,
        filters: filters.hasIiifOnly ? { has_iiif_manifest: true } : {},
        page: 1,
        page_size: 24,
      }
      search.mutate(payload)
    },
    [filters, setQuery, search],
  )

  const prepareRead = useCallback(
    (item: NormalizedItem) => {
      const urls = item.manifest_url ? [item.manifest_url] : []
      setOpenManifestUrls(urls)
      setViewMode('single')
    },
    [setOpenManifestUrls, setViewMode],
  )

  return (
    <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
      <SearchFilters value={filters} onChange={setFilters} />
      <main className="space-y-4">
        <SearchBar initialQuery={query} onSubmit={triggerSearch} />

        {search.isPending && <p className="text-sm text-slate-600">Chargement des résultats...</p>}
        {search.isError && (
          <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">
            Erreur: {search.error.message}
          </p>
        )}

        {!search.isPending && !search.isError && (
          <ResultsGrid
            items={results}
            selectedForComparison={selectedForComparison}
            onPrepareRead={prepareRead}
            onToggleCompare={toggleCompareSelection}
          />
        )}
      </main>
    </div>
  )
}
