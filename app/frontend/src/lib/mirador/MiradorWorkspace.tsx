import { useEffect, useMemo, useRef, useState } from 'react'

import { buildMiradorConfig } from './miradorConfig'

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
  const onStateChangeRef = useRef(onStateChange)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Keep callback ref in sync without triggering effect re-runs
  onStateChangeRef.current = onStateChange

  const stableUrls = useMemo(
    () => Array.from(new Set(manifestUrls.filter((u) => u.length > 0))),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(manifestUrls)],
  )

  useEffect(() => {
    const container = containerRef.current
    if (!container || stableUrls.length === 0) {
      return
    }

    let isMounted = true
    let unsubscribe: (() => void) | undefined
    setIsLoading(true)

    async function mountMirador() {
      try {
        const module = (await import('mirador')) as unknown as { default?: MiradorModule } & MiradorModule
        const mirador = module.default ?? module

        if (!isMounted || !container) {
          return
        }

        const config = buildMiradorConfig({
          manifestUrls: stableUrls,
          initialView,
          showMetadata,
        })

        container.innerHTML = ''
        const instance = mirador.viewer(config, container)

        if (instance.store) {
          unsubscribe = instance.store.subscribe(() => {
            onStateChangeRef.current?.(instance.store?.getState())
          })
        }

        setLoadError(null)
      } catch (error) {
        if (isMounted) {
          setLoadError(error instanceof Error ? error.message : 'Unable to initialize Mirador')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    mountMirador()

    return () => {
      isMounted = false
      unsubscribe?.()
      if (container) {
        container.innerHTML = ''
      }
    }
  }, [stableUrls, initialView, showMetadata])

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

  return (
    <>
      {isLoading && <p className="text-sm text-slate-600">Chargement de Mirador...</p>}
      <div ref={containerRef} className="min-h-[70vh] rounded-md border border-slate-200 bg-white" />
    </>
  )
}
