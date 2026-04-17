import { useMutation } from '@tanstack/react-query'

import { importUrl } from '../lib/apiClient'
import type { ImportRequest, ImportResponse } from '../types/api'

export function useImportUrl() {
  return useMutation<ImportResponse, Error, ImportRequest>({
    mutationFn: (payload) => importUrl(payload),
  })
}
