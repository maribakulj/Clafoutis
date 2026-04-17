import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useImportUrl } from '../hooks/useImportUrl'
import { useReaderStore } from '../store/readerStore'

export function ImportPage() {
  const [url, setUrl] = useState('')
  const navigate = useNavigate()
  const importMutation = useImportUrl()
  const setOpenManifestUrls = useReaderStore((state) => state.setOpenManifestUrls)
  const setViewMode = useReaderStore((state) => state.setViewMode)

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = url.trim()
    if (!trimmed) {
      return
    }
    importMutation.mutate({ url: trimmed })
  }

  const handleOpenInReader = () => {
    const manifest = importMutation.data?.manifest_url
    if (!manifest) {
      return
    }
    setOpenManifestUrls([manifest])
    setViewMode('single')
    navigate('/reader')
  }

  return (
    <section className="mx-auto max-w-2xl space-y-4">
      <header className="space-y-1">
        <h1 className="text-lg font-semibold">Import manuel</h1>
        <p className="text-sm text-slate-600">
          Collez l'URL d'une notice ou d'un manifest IIIF. Le backend tentera de détecter la source
          et de résoudre un manifest IIIF ouvrable dans Mirador.
        </p>
      </header>

      <form className="flex flex-col gap-2 sm:flex-row" onSubmit={handleSubmit}>
        <label htmlFor="import-url" className="sr-only">
          URL à importer
        </label>
        <input
          id="import-url"
          type="url"
          required
          inputMode="url"
          placeholder="https://exemple.org/iiif/manifest.json"
          className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
        />
        <button
          type="submit"
          className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:bg-slate-400"
          disabled={importMutation.isPending}
        >
          {importMutation.isPending ? 'Analyse...' : 'Analyser'}
        </button>
      </form>

      {importMutation.isError && (
        <p
          role="alert"
          className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700"
        >
          Erreur : {importMutation.error.message}
        </p>
      )}

      {importMutation.isSuccess && (
        <div
          role="status"
          className="space-y-2 rounded-md border border-slate-200 bg-white p-4 text-sm"
        >
          <p>
            Source détectée :{' '}
            <span className="font-medium">
              {importMutation.data?.detected_source ?? 'aucune'}
            </span>
          </p>
          {importMutation.data?.manifest_url ? (
            <>
              <p className="break-all text-slate-700">
                Manifest : {importMutation.data.manifest_url}
              </p>
              <button
                type="button"
                className="rounded bg-slate-900 px-3 py-1 text-white"
                onClick={handleOpenInReader}
              >
                Ouvrir dans Mirador
              </button>
            </>
          ) : (
            <p className="text-amber-800">
              Aucun manifest IIIF détecté à partir de cette URL.
            </p>
          )}
        </div>
      )}
    </section>
  )
}
