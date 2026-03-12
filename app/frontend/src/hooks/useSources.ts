import { useQuery } from '@tanstack/react-query'

import { listSources } from '../lib/apiClient'
import type { SourcesResponse } from '../types/api'

export function useSources() {
  return useQuery<SourcesResponse, Error>({
    queryKey: ['sources'],
    queryFn: listSources,
  })
}
