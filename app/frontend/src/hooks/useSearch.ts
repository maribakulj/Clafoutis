import { useRef } from 'react'
import { useMutation } from '@tanstack/react-query'

import { searchItems } from '../lib/apiClient'
import { useSearchStore } from '../store/searchStore'
import type { SearchRequest, SearchResponse } from '../types/api'

export function useSearch() {
  const setResults = useSearchStore((state) => state.setResults)
  const abortRef = useRef<AbortController | null>(null)

  return useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: (payload) => {
      // Cancel any in-flight search before starting a new one
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller
      return searchItems(payload, controller.signal)
    },
    onSuccess: (data) => {
      setResults(data.results)
    },
  })
}
