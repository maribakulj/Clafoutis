import { FormEvent, useEffect, useState } from 'react'

interface SearchBarProps {
  initialQuery: string
  onSubmit: (query: string) => void
}

export function SearchBar({ initialQuery, onSubmit }: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery)

  useEffect(() => {
    setQuery(initialQuery)
  }, [initialQuery])

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = query.trim()
    if (trimmed) {
      onSubmit(trimmed)
    }
  }

  return (
    <form className="flex gap-2" role="search" aria-label="Recherche patrimoniale" onSubmit={handleSubmit}>
      <label htmlFor="search-input" className="sr-only">
        Rechercher un objet patrimonial
      </label>
      <input
        id="search-input"
        className="w-full rounded-md border border-slate-300 bg-white px-3 py-2"
        placeholder="Rechercher un objet patrimonial"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      <button className="rounded-md bg-slate-900 px-4 py-2 text-white" type="submit">
        Rechercher
      </button>
    </form>
  )
}
