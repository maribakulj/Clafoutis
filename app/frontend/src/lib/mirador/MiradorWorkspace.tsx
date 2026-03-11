import { useEffect, useMemo, useRef, useState } from 'react'

import { buildMiradorConfig } from './miradorConfig'

import 'mirador/dist/css/mirador.min.css'

export interface MiradorWorkspaceProps {
  manifestUrls: string[]
  initialView?: 'single' | 'compare'
  showMetadata?: boolean
  onStateChange?: (state: unknown) => void
}

interface MiradorModule {
  viewer: (config: unknown, container: HTMLElement) => {
    store?: {
      getState: () => unknown
      subscribe: (listener: () => void) => () => void
    }
  }
}

/**
 * Mirador-based reading workspace.
 * It receives already-resolved manifest URLs and does not perform discovery logic.
 */
export function MiradorWorkspace({
  manifestUrls,
  initialView = 'single',
  showMetadata = true,
  onStateChange,
}: MiradorWorkspaceProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  const stableUrls = useMemo(
    () => Array.from(new Set(manifestUrls.filter((manifestUrl) => manifestUrl.length > 0))),
    [manifestUrls],
  )

  useEffect(() => {
    if (!containerRef.current || stableUrls.length === 0) {
      return
    }

    let isMounted = true
    let unsubscribe: (() => void) | undefined

    async function mountMirador() {
      try {
        const module = (await import('mirador')) as unknown as { default?: MiradorModule } & MiradorModule
        const mirador = module.default ?? module

        if (!isMounted || !containerRef.current) {
          return
        }

        const config = buildMiradorConfig({
          manifestUrls: stableUrls,
          initialView,
          showMetadata,
        })

        containerRef.current.innerHTML = ''
        const instance = mirador.viewer(config, containerRef.current)

        if (onStateChange && instance.store) {
          unsubscribe = instance.store.subscribe(() => {
            onStateChange(instance.store?.getState())
          })
        }

        setLoadError(null)
      } catch (error) {
        if (isMounted) {
          setLoadError(error instanceof Error ? error.message : 'Unable to initialize Mirador')
        }
      }
    }

    mountMirador()

    return () => {
      isMounted = false
      if (unsubscribe) {
        unsubscribe()
      }
      if (containerRef.current) {
        containerRef.current.innerHTML = ''
      }
    }
  }, [stableUrls, initialView, showMetadata, onStateChange])

  if (stableUrls.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-slate-300 p-6 text-sm text-slate-600">
        Aucun manifest ouvert. Revenez à la recherche pour préparer une lecture.
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-700">
        Impossible de charger Mirador : {loadError}
      </div>
    )
  }

  return <div ref={containerRef} className="min-h-[70vh] rounded-md border border-slate-200 bg-white" />
}
