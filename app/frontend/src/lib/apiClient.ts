import type {
  ImportRequest,
  ImportResponse,
  SearchRequest,
  SearchResponse,
  SourcesResponse,
} from '../types/api'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const REQUEST_TIMEOUT_MS = 30_000

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      signal: init?.signal ?? controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
    })

    if (!response.ok) {
      const body = await response.text()
      throw new Error(body || `${response.status} ${response.statusText}`)
    }

    return (await response.json()) as T
  } finally {
    clearTimeout(timeoutId)
  }
}

export async function searchItems(
  payload: SearchRequest,
  signal?: AbortSignal,
): Promise<SearchResponse> {
  return request<SearchResponse>('/api/search', {
    method: 'POST',
    body: JSON.stringify(payload),
    signal,
  })
}

export async function listSources(): Promise<SourcesResponse> {
  return request<SourcesResponse>('/api/sources')
}

export async function importUrl(
  payload: ImportRequest,
  signal?: AbortSignal,
): Promise<ImportResponse> {
  return request<ImportResponse>('/api/import', {
    method: 'POST',
    body: JSON.stringify(payload),
    signal,
  })
}
