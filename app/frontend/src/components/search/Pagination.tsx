interface PaginationProps {
  page: number
  hasNextPage: boolean
  totalEstimated: number
  pageSize: number
  resultsCount: number
  disabled?: boolean
  onPageChange: (page: number) => void
}

export function Pagination({
  page,
  hasNextPage,
  totalEstimated,
  pageSize,
  resultsCount,
  disabled,
  onPageChange,
}: PaginationProps) {
  if (resultsCount === 0 && page === 1) {
    return null
  }
  const canPrev = page > 1 && !disabled
  const canNext = hasNextPage && !disabled

  return (
    <nav
      className="flex items-center justify-between gap-3 rounded-md border border-slate-200 bg-white p-2 text-sm"
      aria-label="Pagination des résultats"
    >
      <p className="text-slate-600">
        Page {page}
        {totalEstimated > 0 ? ` · ~${totalEstimated} résultats estimés` : ''}
        {resultsCount > 0 ? ` · ${resultsCount} affichés` : ''}
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          className="rounded border border-slate-300 px-3 py-1 disabled:text-slate-400"
          disabled={!canPrev}
          onClick={() => canPrev && onPageChange(page - 1)}
        >
          Précédent
        </button>
        <button
          type="button"
          className="rounded border border-slate-300 px-3 py-1 disabled:text-slate-400"
          disabled={!canNext}
          onClick={() => canNext && onPageChange(page + 1)}
          aria-label={`Aller à la page ${page + 1}`}
        >
          Suivant
        </button>
      </div>
      <span className="sr-only" aria-live="polite">
        Page {page} affichée, page {pageSize ? page + 1 : page + 1} {canNext ? 'disponible' : 'non disponible'}
      </span>
    </nav>
  )
}
