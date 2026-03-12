import type {
  ImportRequest,
  ImportResponse,
  SearchRequest,
  SearchResponse,
  SourcesResponse,
} from '../types/api'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://localhost:8000' : '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    const fallback = `${response.status} ${response.statusText}`
    throw new Error((await response.text()) || fallback)
  }

  return (await response.json()) as T
}

export async function searchItems(payload: SearchRequest): Promise<SearchResponse> {
  return request<SearchResponse>('/api/search', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function listSources(): Promise<SourcesResponse> {
  return request<SourcesResponse>('/api/sources')
}

export async function importByUrl(payload: ImportRequest): Promise<ImportResponse> {
  return request<ImportResponse>('/api/import', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
