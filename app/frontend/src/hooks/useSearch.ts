import { useRef } from 'react'
import { useMutation } from '@tanstack/react-query'

import { searchItems } from '../lib/apiClient'
import { useSearchStore } from '../store/searchStore'
import type { SearchRequest, SearchResponse } from '../types/api'

export function useSearch() {
  const setResults = useSearchStore((state) => state.setResults)
  const setPageMeta = useSearchStore((state) => state.setPageMeta)
  const abortRef = useRef<AbortController | null>(null)

  return useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: (payload) => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller
      return searchItems(payload, controller.signal)
    },
    onSuccess: (data) => {
      setResults(data.results)
      setPageMeta({
        page: data.page,
        hasNextPage: data.has_next_page,
        totalEstimated: data.total_estimated,
        partialFailures: data.partial_failures,
        sourcesUsed: data.sources_used,
      })
    },
  })
}
