import { useMutation } from '@tanstack/react-query'

import { searchItems } from '../lib/apiClient'
import { useSearchStore } from '../store/searchStore'
import type { SearchRequest, SearchResponse } from '../types/api'

export function useSearch() {
  const setResults = useSearchStore((state) => state.setResults)

  return useMutation<SearchResponse, Error, SearchRequest>({
    mutationFn: searchItems,
    onSuccess: (data) => {
      setResults(data.results)
    },
  })
}
