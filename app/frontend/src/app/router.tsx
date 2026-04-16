import { NavLink, Navigate, Route, Routes } from 'react-router-dom'

import { AboutPage } from '../pages/AboutPage'
import { ImportPage } from '../pages/ImportPage'
import { ReaderPage } from '../pages/ReaderPage'
import { SearchPage } from '../pages/SearchPage'
import { SourcesPage } from '../pages/SourcesPage'

function navClass({ isActive }: { isActive: boolean }) {
  return `rounded px-2 py-1 ${isActive ? 'bg-slate-900 text-white' : 'bg-slate-100 hover:bg-slate-200'}`
}

function NotFoundPage() {
  return (
    <section className="space-y-2">
      <h1 className="text-lg font-semibold">Page introuvable</h1>
      <p className="text-sm text-slate-600">La page demandée n'existe pas.</p>
    </section>
  )
}

function AppLayout() {
  return (
    <div className="mx-auto min-h-screen max-w-7xl p-4">
      <header className="mb-6 rounded-md border border-slate-200 bg-white p-3">
        <nav className="flex flex-wrap gap-3 text-sm">
          <NavLink className={navClass} to="/search">
            Recherche
          </NavLink>
          <NavLink className={navClass} to="/reader">
            Lecture
          </NavLink>
          <NavLink className={navClass} to="/import">
            Import
          </NavLink>
          <NavLink className={navClass} to="/sources">
            Sources
          </NavLink>
          <NavLink className={navClass} to="/about">
            À propos
          </NavLink>
        </nav>
      </header>
      <Routes>
        <Route element={<Navigate replace to="/search" />} path="/" />
        <Route element={<SearchPage />} path="/search" />
        <Route element={<ReaderPage />} path="/reader" />
        <Route element={<ImportPage />} path="/import" />
        <Route element={<SourcesPage />} path="/sources" />
        <Route element={<AboutPage />} path="/about" />
        <Route element={<NotFoundPage />} path="*" />
      </Routes>
    </div>
  )
}

export function AppRouter() {
  return <AppLayout />
}
