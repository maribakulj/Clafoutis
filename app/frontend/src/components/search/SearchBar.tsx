import { FormEvent, useState } from 'react'

interface SearchBarProps {
  initialQuery: string
  onSubmit: (query: string) => void
}

export function SearchBar({ initialQuery, onSubmit }: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery)

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSubmit(query.trim())
  }

  return (
    <form className="flex gap-2" onSubmit={handleSubmit}>
      <input
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
