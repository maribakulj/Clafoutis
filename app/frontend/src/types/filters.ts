export interface SearchFilters {
  sources: string[]
  hasIiifOnly: boolean
}

export const defaultSearchFilters: SearchFilters = {
  sources: [],
  hasIiifOnly: false,
}
