import { memo, useState } from 'react'

import type { NormalizedItem } from '../../types/normalized'

interface ResultCardProps {
  item: NormalizedItem
  selected: boolean
  onToggleCompare: (itemId: string) => void
  onPrepareRead: (item: NormalizedItem) => void
}

function Badge({ children, tone = 'slate' }: { children: React.ReactNode; tone?: 'slate' | 'emerald' | 'indigo' }) {
  const toneClasses: Record<string, string> = {
    slate: 'bg-slate-100 text-slate-700 border-slate-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    indigo: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  }
  return (
    <span className={`inline-block rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-wide ${toneClasses[tone]}`}>
      {children}
    </span>
  )
}

export const ResultCard = memo(function ResultCard({
  item,
  selected,
  onToggleCompare,
  onPrepareRead,
}: ResultCardProps) {
  const [thumbFailed, setThumbFailed] = useState(false)

  const hasThumbnail = !!item.thumbnail_url && !thumbFailed
  const canRead = !!item.manifest_url
  const creatorLine = item.creators.length > 0 ? item.creators.join(', ') : null

  return (
    <article
      className="flex flex-col gap-2 rounded-md border border-slate-200 bg-white p-3 shadow-sm"
      aria-label={item.title}
    >
      <div className="aspect-[4/3] w-full overflow-hidden rounded bg-slate-100">
        {hasThumbnail ? (
          <img
            src={item.thumbnail_url as string}
            alt=""
            loading="lazy"
            className="h-full w-full object-cover"
            onError={() => setThumbFailed(true)}
          />
        ) : (
          <div
            className="flex h-full w-full items-center justify-center text-[10px] uppercase tracking-wide text-slate-400"
            role="img"
            aria-label="Aperçu indisponible"
          >
            Pas de miniature
          </div>
        )}
      </div>

      <h3 className="line-clamp-2 text-sm font-semibold">{item.title}</h3>

      <dl className="space-y-0.5 text-xs text-slate-600">
        <div className="flex gap-1">
          <dt className="sr-only">Source</dt>
          <dd>{item.source_label}</dd>
        </div>
        <div className="flex gap-1">
          <dt className="sr-only">Institution</dt>
          <dd>{item.institution ?? 'Institution inconnue'}</dd>
        </div>
        {creatorLine && (
          <div className="flex gap-1">
            <dt className="sr-only">Créateurs</dt>
            <dd className="line-clamp-1">{creatorLine}</dd>
          </div>
        )}
        {item.date_display && (
          <div className="flex gap-1">
            <dt className="sr-only">Date</dt>
            <dd>{item.date_display}</dd>
          </div>
        )}
      </dl>

      <div className="flex flex-wrap gap-1">
        {item.object_type && item.object_type !== 'other' && <Badge>{item.object_type}</Badge>}
        {item.has_iiif_manifest && <Badge tone="emerald">IIIF</Badge>}
        {item.has_ocr && <Badge tone="indigo">OCR</Badge>}
      </div>

      <div className="mt-auto flex flex-wrap gap-2 pt-1">
        <button
          className="rounded bg-slate-900 px-2 py-1 text-xs text-white disabled:bg-slate-400"
          type="button"
          disabled={!canRead}
          aria-label={
            canRead
              ? `Préparer la lecture de ${item.title}`
              : `Aucun manifest disponible pour ${item.title}`
          }
          title={canRead ? undefined : 'Aucun manifest IIIF disponible'}
          onClick={() => onPrepareRead(item)}
        >
          Préparer lecture
        </button>
        <button
          className="rounded border border-slate-300 px-2 py-1 text-xs disabled:text-slate-400"
          type="button"
          disabled={!canRead}
          aria-label={selected ? `Retirer ${item.title} de la comparaison` : `Comparer ${item.title}`}
          onClick={() => onToggleCompare(item.id)}
        >
          {selected ? 'Retirer comparaison' : 'Comparer'}
        </button>
        {item.record_url && (
          <a
            className="rounded border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-50"
            href={item.record_url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Ouvrir la notice d'origine de ${item.title} dans un nouvel onglet`}
          >
            Voir notice ↗
          </a>
        )}
      </div>
    </article>
  )
})
