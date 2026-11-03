import { useEffect, useState } from 'react'

import { AdvisorChat } from './components/AdvisorChat'
import { ForecastDashboard } from './components/ForecastDashboard'
import { InventoryDashboard } from './components/InventoryDashboard'

import './App.css'

type ApiStatus = 'checking' | 'online' | 'offline'

const NAVIGATION = [
  { href: '#previsao', label: 'Previsão de demanda' },
  { href: '#estoque', label: 'Estoque' },
  { href: '#assistente', label: 'Assistente de IA' },
]

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
      <a className="skip-link" href="#conteudo">
        Pular para o conteúdo
      </a>

      <header className="app-header">
        <a
          className="brand"
          href="#inicio"
          aria-label="DemandPilot AI — início"
        >
          <span className="brand-mark">D</span>

          <span className="brand-name">
            <strong>DemandPilot</strong>
            <span>AI</span>
          </span>
        </a>

        <nav
          className="app-navigation"
          aria-label="Navegação principal"
        >
          {NAVIGATION.map((item) => (
            <a key={item.href} href={item.href}>
              {item.label}
            </a>
          ))}
        </nav>

        <div
          className={`api-status api-status--${apiStatus}`}
          role="status"
        >
          <span className="status-dot" aria-hidden="true" />
          {statusLabel}
        </div>
      </header>

      <main id="conteudo" className="main-content">
        <section className="hero" id="inicio">
          <div className="eyebrow">
            INTELIGÊNCIA PARA RESTAURANTES
          </div>

          <h1>
            Decisões melhores,
            <br />
            orientadas por dados.
          </h1>

          <p>
            Preveja a demanda dos produtos, antecipe faltas de
            ingredientes e transforme dados operacionais em
            informações úteis para seu restaurante.
          </p>

          <div className="hero-meta">
            <span>Machine Learning</span>
            <span
              className="meta-separator"
              aria-hidden="true"
            />
            <span>Planejamento de estoque</span>
            <span
              className="meta-separator"
              aria-hidden="true"
            />
            <span>IA Generativa</span>
          </div>
        </section>

        <div id="previsao" className="dashboard-anchor">
          <ForecastDashboard />
        </div>

        <div id="estoque" className="dashboard-anchor">
          <InventoryDashboard restaurantId={1} />
        </div>

        <div id="assistente" className="dashboard-anchor">
          <AdvisorChat restaurantId={1} />
        </div>
      </main>

      <footer className="app-footer">
        <span>DemandPilot AI</span>
        <span>Machine Learning + IA Generativa</span>
      </footer>
    </div>
  )
}

export default App