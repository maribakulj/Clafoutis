import { create } from 'zustand'

import type { NormalizedItem } from '../types/normalized'
import type { PartialFailure } from '../types/api'
import type { SearchFilters } from '../types/filters'
import { defaultSearchFilters } from '../types/filters'

interface SearchState {
  query: string
  filters: SearchFilters
  results: NormalizedItem[]
  selectedForComparison: string[]
  page: number
  pageSize: number
  hasNextPage: boolean
  totalEstimated: number
  partialFailures: PartialFailure[]
  sourcesUsed: string[]
  setQuery: (query: string) => void
  setFilters: (filters: SearchFilters) => void
  setResults: (items: NormalizedItem[]) => void
  setPage: (page: number) => void
  setPageMeta: (meta: {
    page: number
    hasNextPage: boolean
    totalEstimated: number
    partialFailures: PartialFailure[]
    sourcesUsed: string[]
  }) => void
  toggleCompareSelection: (itemId: string) => void
  clearCompareSelection: () => void
}

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  filters: defaultSearchFilters,
  results: [],
  selectedForComparison: [],
  page: 1,
  pageSize: 24,
  hasNextPage: false,
  totalEstimated: 0,
  partialFailures: [],
  sourcesUsed: [],
  setQuery: (query) => set({ query }),
  setFilters: (filters) => set({ filters, page: 1 }),
  setResults: (results) => set({ results }),
  setPage: (page) => set({ page }),
  setPageMeta: ({ page, hasNextPage, totalEstimated, partialFailures, sourcesUsed }) =>
    set({ page, hasNextPage, totalEstimated, partialFailures, sourcesUsed }),
  toggleCompareSelection: (itemId) =>
    set((state) => {
      const isSelected = state.selectedForComparison.includes(itemId)
      return {
        selectedForComparison: isSelected
          ? state.selectedForComparison.filter((id) => id !== itemId)
          : [...state.selectedForComparison, itemId],
      }
    }),
  clearCompareSelection: () => set({ selectedForComparison: [] }),
}))
