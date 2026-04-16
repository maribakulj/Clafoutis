import { ResultCard } from '../results/ResultCard'
import type { NormalizedItem } from '../../types/normalized'

interface ResultsGridProps {
  items: NormalizedItem[]
  selectedForComparison: string[]
  onToggleCompare: (itemId: string) => void
  onPrepareRead: (item: NormalizedItem) => void
}

export function ResultsGrid({
  items,
  selectedForComparison,
  onToggleCompare,
  onPrepareRead,
}: ResultsGridProps) {
  if (items.length === 0) {
    return (
      <p className="rounded-md border border-dashed border-slate-300 p-6 text-sm" role="status">
        Aucun résultat.
      </p>
    )
  }

  return (
    <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3" aria-label={`${items.length} résultats`}>
      {items.map((item) => (
        <ResultCard
          key={item.id}
          item={item}
          selected={selectedForComparison.includes(item.id)}
          onPrepareRead={onPrepareRead}
          onToggleCompare={onToggleCompare}
        />
      ))}
    </section>
  )
}
