import { memo } from 'react'

import type { NormalizedItem } from '../../types/normalized'

interface ResultCardProps {
  item: NormalizedItem
  selected: boolean
  onToggleCompare: (itemId: string) => void
  onPrepareRead: (item: NormalizedItem) => void
}

export const ResultCard = memo(function ResultCard({
  item,
  selected,
  onToggleCompare,
  onPrepareRead,
}: ResultCardProps) {
  return (
    <article className="rounded-md border border-slate-200 bg-white p-4 shadow-sm" aria-label={item.title}>
      <h3 className="mb-1 line-clamp-2 text-sm font-semibold">{item.title}</h3>
      <p className="text-xs text-slate-600">{item.source_label}</p>
      <p className="text-xs text-slate-600">{item.institution ?? 'Institution inconnue'}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          className="rounded bg-slate-900 px-2 py-1 text-xs text-white"
          type="button"
          aria-label={`Préparer la lecture de ${item.title}`}
          onClick={() => onPrepareRead(item)}
        >
          Préparer lecture
        </button>
        <button
          className="rounded border border-slate-300 px-2 py-1 text-xs"
          type="button"
          aria-label={selected ? `Retirer ${item.title} de la comparaison` : `Comparer ${item.title}`}
          onClick={() => onToggleCompare(item.id)}
        >
          {selected ? 'Retirer comparaison' : 'Comparer'}
        </button>
      </div>
    </article>
  )
})
