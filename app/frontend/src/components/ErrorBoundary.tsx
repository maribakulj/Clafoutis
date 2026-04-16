import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="rounded-md border border-red-300 bg-red-50 p-6 text-sm text-red-700">
          <h2 className="mb-2 font-semibold">Une erreur est survenue</h2>
          <p>{this.state.error.message}</p>
          <button
            className="mt-3 rounded bg-red-600 px-3 py-1 text-white"
            type="button"
            onClick={() => this.setState({ error: null })}
          >
            Réessayer
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
