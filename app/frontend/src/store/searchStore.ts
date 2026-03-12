import { create } from 'zustand'

import type { NormalizedItem } from '../types/normalized'
import type { SearchFilters } from '../types/filters'
import { defaultSearchFilters } from '../types/filters'

interface SearchState {
  query: string
  filters: SearchFilters
  results: NormalizedItem[]
  selectedForComparison: string[]
  setQuery: (query: string) => void
  setFilters: (filters: SearchFilters) => void
  setResults: (items: NormalizedItem[]) => void
  toggleCompareSelection: (itemId: string) => void
  clearCompareSelection: () => void
}

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  filters: defaultSearchFilters,
  results: [],
  selectedForComparison: [],
  setQuery: (query) => set({ query }),
  setFilters: (filters) => set({ filters }),
  setResults: (results) => set({ results }),
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
