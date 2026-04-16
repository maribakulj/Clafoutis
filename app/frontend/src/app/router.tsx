import { lazy, Suspense } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'

import { ErrorBoundary } from '../components/ErrorBoundary'

const SearchPage = lazy(() => import('../pages/SearchPage').then((m) => ({ default: m.SearchPage })))
const ReaderPage = lazy(() => import('../pages/ReaderPage').then((m) => ({ default: m.ReaderPage })))
const ImportPage = lazy(() => import('../pages/ImportPage').then((m) => ({ default: m.ImportPage })))
const SourcesPage = lazy(() => import('../pages/SourcesPage').then((m) => ({ default: m.SourcesPage })))
const AboutPage = lazy(() => import('../pages/AboutPage').then((m) => ({ default: m.AboutPage })))

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

function PageFallback() {
  return <p className="text-sm text-slate-600">Chargement...</p>
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
      <ErrorBoundary>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route element={<Navigate replace to="/search" />} path="/" />
            <Route element={<SearchPage />} path="/search" />
            <Route element={<ReaderPage />} path="/reader" />
            <Route element={<ImportPage />} path="/import" />
            <Route element={<SourcesPage />} path="/sources" />
            <Route element={<AboutPage />} path="/about" />
            <Route element={<NotFoundPage />} path="*" />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </div>
  )
}

export function AppRouter() {
  return <AppLayout />
}
