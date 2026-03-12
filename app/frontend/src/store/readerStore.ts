import { create } from 'zustand'

interface ReaderConfig {
  viewMode: 'single' | 'compare'
  showMetadata: boolean
}

interface ReaderState {
  openManifestUrls: string[]
  readerConfig: ReaderConfig
  setOpenManifestUrls: (urls: string[]) => void
  setViewMode: (mode: ReaderConfig['viewMode']) => void
  setShowMetadata: (enabled: boolean) => void
}

export const useReaderStore = create<ReaderState>((set) => ({
  openManifestUrls: [],
  readerConfig: { viewMode: 'single', showMetadata: true },
  setOpenManifestUrls: (openManifestUrls) => set({ openManifestUrls }),
  setViewMode: (mode) => set((state) => ({ readerConfig: { ...state.readerConfig, viewMode: mode } })),
  setShowMetadata: (enabled) =>
    set((state) => ({ readerConfig: { ...state.readerConfig, showMetadata: enabled } })),
}))
