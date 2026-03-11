export interface MiradorWorkspaceConfigOptions {
  manifestUrls: string[]
  initialView?: 'single' | 'compare'
  showMetadata?: boolean
}

interface MiradorWindow {
  manifestId: string
}

interface MiradorCatalogItem {
  manifestId: string
}

interface MiradorWorkspace {
  showZoomControls: boolean
}

interface MiradorConfig {
  id: string
  windows: MiradorWindow[]
  catalog: MiradorCatalogItem[]
  workspace: MiradorWorkspace
  workspaceControlPanel: {
    enabled: boolean
  }
  sideBarOpenByDefault: boolean
}

/**
 * Build a minimal Mirador config focused on reading provided manifests.
 */
export function buildMiradorConfig({
  manifestUrls,
  initialView = 'single',
  showMetadata = true,
}: MiradorWorkspaceConfigOptions): MiradorConfig {
  const windows = manifestUrls.map((manifestId) => ({ manifestId }))

  return {
    id: 'mirador-root',
    windows,
    catalog: manifestUrls.map((manifestId) => ({ manifestId })),
    workspace: {
      showZoomControls: true,
    },
    workspaceControlPanel: {
      enabled: initialView === 'compare',
    },
    sideBarOpenByDefault: showMetadata,
  }
}
