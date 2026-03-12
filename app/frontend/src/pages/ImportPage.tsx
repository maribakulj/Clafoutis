import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { importByUrl } from '../lib/apiClient'
import { useReaderStore } from '../store/readerStore'

export function ImportPage() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<{
    detectedSource: string | null
    recordUrl: string | null
    manifestUrl: string | null
  } | null>(null)

  const setOpenManifestUrls = useReaderStore((state) => state.setOpenManifestUrls)
  const setViewMode = useReaderStore((state) => state.setViewMode)

  const navigate = useNavigate()

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = url.trim()
    if (!trimmed) {
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await importByUrl({ url: trimmed })
      setResult({
        detectedSource: response.detected_source,
        recordUrl: response.record_url,
        manifestUrl: response.manifest_url,
      })

      if (response.manifest_url) {
        setOpenManifestUrls([response.manifest_url])
        setViewMode('single')
      }
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : 'Erreur d’import')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="space-y-4">
      <h1 className="text-lg font-semibold">Import manuel</h1>
      <p className="text-sm text-slate-600">
        Collez une URL de manifest IIIF ou une URL de notice, puis laissez le backend tenter la
        résolution vers un manifest.
      </p>

      <form className="space-y-3 rounded-md border border-slate-200 bg-white p-4" onSubmit={handleSubmit}>
        <label className="block text-sm font-medium" htmlFor="import-url">
          URL
        </label>
        <input
          id="import-url"
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="https://..."
          value={url}
          onChange={(event) => setUrl(event.target.value)}
        />
        <button
          className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-60"
          disabled={loading}
          type="submit"
        >
          {loading ? 'Import en cours…' : 'Importer'}
        </button>
      </form>

      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</p>
      )}

      {result && (
        <div className="space-y-2 rounded-md border border-slate-200 bg-white p-4 text-sm">
          <p>
            <span className="font-medium">Source détectée :</span> {result.detectedSource ?? 'inconnue'}
          </p>
          <p>
            <span className="font-medium">URL notice :</span> {result.recordUrl ?? 'n/a'}
          </p>
          <p>
            <span className="font-medium">Manifest résolu :</span> {result.manifestUrl ?? 'non trouvé'}
          </p>

          {result.manifestUrl && (
            <button
              className="rounded border border-slate-300 px-3 py-1"
              type="button"
              onClick={() => navigate('/reader')}
            >
              Ouvrir dans Lecture
            </button>
          )}
        </div>
      )}
    </section>
  )
}
