import { useCallback } from 'react'

import { Pagination } from '../components/search/Pagination'
import { PartialFailuresBanner } from '../components/search/PartialFailuresBanner'
import { ResultsGrid } from '../components/search/ResultsGrid'
import { SearchBar } from '../components/search/SearchBar'
import { SearchFilters } from '../components/search/SearchFilters'
import { useSearch } from '../hooks/useSearch'
import { useReaderStore } from '../store/readerStore'
import { useSearchStore } from '../store/searchStore'
import type { SearchRequest } from '../types/api'
import type { NormalizedItem } from '../types/normalized'

export function SearchPage() {
  const query = useSearchStore((state) => state.query)
  const filters = useSearchStore((state) => state.filters)
  const results = useSearchStore((state) => state.results)
  const page = useSearchStore((state) => state.page)
  const pageSize = useSearchStore((state) => state.pageSize)
  const hasNextPage = useSearchStore((state) => state.hasNextPage)
  const totalEstimated = useSearchStore((state) => state.totalEstimated)
  const partialFailures = useSearchStore((state) => state.partialFailures)
  const selectedForComparison = useSearchStore((state) => state.selectedForComparison)
  const setQuery = useSearchStore((state) => state.setQuery)
  const setFilters = useSearchStore((state) => state.setFilters)
  const toggleCompareSelection = useSearchStore((state) => state.toggleCompareSelection)

  const setOpenManifestUrls = useReaderStore((state) => state.setOpenManifestUrls)
  const setViewMode = useReaderStore((state) => state.setViewMode)

  const search = useSearch()

  const runSearch = useCallback(
    (nextQuery: string, nextPage: number) => {
      const trimmed = nextQuery.trim()
      if (!trimmed) {
        return
      }
      const payload: SearchRequest = {
        query: trimmed,
        sources: filters.sources.length > 0 ? filters.sources : undefined,
        filters: {
          has_iiif_manifest: filters.hasIiifOnly ? true : null,
        },
        page: nextPage,
        page_size: pageSize,
      }
      search.mutate(payload)
    },
    [filters, pageSize, search],
  )

  const triggerSearch = useCallback(
    (nextQuery: string) => {
      setQuery(nextQuery)
      runSearch(nextQuery, 1)
    },
    [runSearch, setQuery],
  )

  const handlePageChange = useCallback(
    (nextPage: number) => {
      runSearch(query, nextPage)
    },
    [runSearch, query],
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

        {search.isPending && <p className="text-sm text-slate-600" role="status">Chargement des résultats...</p>}
        {search.isError && (
          <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700" role="alert">
            Erreur: {search.error.message}
          </p>
        )}

        <PartialFailuresBanner failures={partialFailures} />

        {!search.isPending && !search.isError && (
          <>
            <ResultsGrid
              items={results}
              selectedForComparison={selectedForComparison}
              onPrepareRead={prepareRead}
              onToggleCompare={toggleCompareSelection}
            />
            <Pagination
              page={page}
              hasNextPage={hasNextPage}
              totalEstimated={totalEstimated}
              pageSize={pageSize}
              resultsCount={results.length}
              disabled={search.isPending}
              onPageChange={handlePageChange}
            />
          </>
        )}
      </main>
    </div>
  )
}
