import { useSources } from '../../hooks/useSources'
import type { SearchFilters as SearchFiltersType } from '../../types/filters'

interface SearchFiltersProps {
  value: SearchFiltersType
  onChange: (filters: SearchFiltersType) => void
}

export function SearchFilters({ value, onChange }: SearchFiltersProps) {
  const sourcesQuery = useSources()

  return (
    <aside className="space-y-4 rounded-md border border-slate-200 bg-white p-4" aria-label="Filtres de recherche">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-600">Filtres</h2>

      <fieldset>
        <legend className="mb-2 text-sm font-medium">Sources</legend>
        <div className="space-y-2">
          {(sourcesQuery.data?.sources ?? []).map((source) => {
            const checked = value.sources.includes(source.name)
            return (
              <label key={source.name} className="flex items-center gap-2 text-sm">
                <input
                  checked={checked}
                  type="checkbox"
                  onChange={(event) => {
                    const nextSources = event.target.checked
                      ? [...value.sources, source.name]
                      : value.sources.filter((candidate) => candidate !== source.name)
                    onChange({ ...value, sources: nextSources })
                  }}
                />
                {source.label}
              </label>
            )
          })}
        </div>
      </fieldset>

      <label className="flex items-center gap-2 text-sm">
        <input
          checked={value.hasIiifOnly}
          type="checkbox"
          onChange={(event) => onChange({ ...value, hasIiifOnly: event.target.checked })}
        />
        IIIF uniquement
      </label>
    </aside>
  )
}
