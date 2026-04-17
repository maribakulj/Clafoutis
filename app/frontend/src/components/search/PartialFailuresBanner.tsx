import type { PartialFailure } from '../../types/api'

interface PartialFailuresBannerProps {
  failures: PartialFailure[]
}

const STATUS_LABELS: Record<PartialFailure['status'], string> = {
  degraded: 'dégradé',
  error: 'erreur',
}

export function PartialFailuresBanner({ failures }: PartialFailuresBannerProps) {
  if (failures.length === 0) {
    return null
  }
  return (
    <div
      role="status"
      className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900"
      aria-label="Sources partiellement indisponibles"
    >
      <p className="mb-1 font-semibold">Certaines sources n'ont pas pu répondre complètement :</p>
      <ul className="list-disc space-y-0.5 pl-5">
        {failures.map((failure, index) => (
          <li key={`${failure.source}-${index}`}>
            <span className="font-medium">{failure.source}</span>
            {' — '}
            {STATUS_LABELS[failure.status]}
            {failure.error ? ` (${failure.error})` : null}
          </li>
        ))}
      </ul>
    </div>
  )
}
