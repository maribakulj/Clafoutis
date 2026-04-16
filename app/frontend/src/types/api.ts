import type { NormalizedItem } from './normalized'

export interface PartialFailure {
  source: string
  status: 'degraded' | 'error'
  error: string | null
}

export interface SearchRequest {
  query: string
  sources?: string[]
  filters: Record<string, unknown>
  page: number
  page_size: number
}

export interface SearchResponse {
  query: string
  page: number
  page_size: number
  total_estimated: number
  has_next_page: boolean
  results: NormalizedItem[]
  sources_used: string[]
  partial_failures: PartialFailure[]
  duration_ms: number
}

export interface SourceCapabilities {
  search: boolean
  get_item: boolean
  resolve_manifest: boolean
}

export interface SourceDescriptor {
  name: string
  label: string
  source_type: string
  capabilities: SourceCapabilities
  healthy: boolean
  notes: string | null
}

export interface SourcesResponse {
  sources: SourceDescriptor[]
}

export interface ApiError {
  error: string
  details: string | null
}
