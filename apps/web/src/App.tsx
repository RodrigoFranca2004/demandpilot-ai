import { useEffect, useState } from 'react'

import { AdvisorChat } from './components/AdvisorChat'
import { ForecastDashboard } from './components/ForecastDashboard'
import { InventoryDashboard } from './components/InventoryDashboard'

import './App.css'

type ApiStatus = 'checking' | 'online' | 'offline'

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>('checking')

  useEffect(() => {
    const controller = new AbortController()

    async function checkApiHealth() {
      try {
        const response = await fetch('/api/health', {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error('Backend health check failed')
        }

        if (!controller.signal.aborted) {
          setApiStatus('online')
        }
      } catch {
        if (!controller.signal.aborted) {
          setApiStatus('offline')
        }
      }
    }

    void checkApiHealth()

    return () => controller.abort()
  }, [])

  const statusLabel = {
    checking: 'Verificando conexão',
    online: 'API conectada',
    offline: 'API indisponível',
  }[apiStatus]

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">D</span>

          <div className="brand-name">
            <strong>DemandPilot</strong>
            <span>AI</span>
          </div>
        </div>

        <div
          className={`api-status api-status--${apiStatus}`}
          role="status"
        >
          <span className="status-dot" aria-hidden="true" />
          {statusLabel}
        </div>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="eyebrow">RESTAURANT INTELLIGENCE</div>

          <h1>
            Better decisions,
            <br />
            powered by data.
          </h1>

          <p>
            Forecast product demand, anticipate inventory shortages,
            and turn operational data into actionable insights.
          </p>

          <div className="hero-meta">
            <span>Machine Learning</span>
            <span className="meta-separator" aria-hidden="true" />
            <span>Inventory Analytics</span>
            <span className="meta-separator" aria-hidden="true" />
            <span>Generative AI</span>
          </div>
        </section>

        <ForecastDashboard />

        <InventoryDashboard restaurantId={1} />

        <AdvisorChat restaurantId={1} />
      </main>

      <footer className="app-footer">
        <span>DemandPilot AI</span>
        <span>Machine Learning + Generative AI</span>
      </footer>
    </div>
  )
}

export default App