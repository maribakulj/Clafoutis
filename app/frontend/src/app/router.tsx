import { Link, Navigate, Route, Routes } from 'react-router-dom'

import { AboutPage } from '../pages/AboutPage'
import { ImportPage } from '../pages/ImportPage'
import { ReaderPage } from '../pages/ReaderPage'
import { SearchPage } from '../pages/SearchPage'
import { SourcesPage } from '../pages/SourcesPage'

function AppLayout() {
  return (
    <div className="mx-auto min-h-screen max-w-7xl p-4">
      <header className="mb-6 rounded-md border border-slate-200 bg-white p-3">
        <nav className="flex flex-wrap gap-3 text-sm">
          <Link className="rounded bg-slate-100 px-2 py-1 hover:bg-slate-200" to="/search">
            Recherche
          </Link>
          <Link className="rounded bg-slate-100 px-2 py-1 hover:bg-slate-200" to="/reader">
            Lecture
          </Link>
          <Link className="rounded bg-slate-100 px-2 py-1 hover:bg-slate-200" to="/import">
            Import
          </Link>
          <Link className="rounded bg-slate-100 px-2 py-1 hover:bg-slate-200" to="/sources">
            Sources
          </Link>
          <Link className="rounded bg-slate-100 px-2 py-1 hover:bg-slate-200" to="/about">
            À propos
          </Link>
        </nav>
      </header>
      <Routes>
        <Route element={<Navigate replace to="/search" />} path="/" />
        <Route element={<SearchPage />} path="/search" />
        <Route element={<ReaderPage />} path="/reader" />
        <Route element={<ImportPage />} path="/import" />
        <Route element={<SourcesPage />} path="/sources" />
        <Route element={<AboutPage />} path="/about" />
      </Routes>
    </div>
  )
}

export function AppRouter() {
  return <AppLayout />
}
