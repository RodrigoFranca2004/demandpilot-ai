import { useEffect, useRef, useState } from 'react'

import { getDemoSettings, refreshDemoSales, type DemoSettings } from './api/demo'

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
  const [menuOpen, setMenuOpen] = useState(false)
  const menuToggle = useRef<HTMLButtonElement>(null)
  const [demo, setDemo] = useState<DemoSettings | null>(null)
  const [demoError, setDemoError] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshMessage, setRefreshMessage] = useState('')
  const [salesRevision, setSalesRevision] = useState(0)

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

        const payload: unknown = await response.json()
        if (
          typeof payload !== 'object' ||
          payload === null ||
          !('status' in payload) ||
          payload.status !== 'ok'
        ) {
          throw new Error('Unexpected response from backend health check')
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

  useEffect(() => {
    const controller = new AbortController()

    void getDemoSettings(controller.signal)
      .then((settings) => {
        if (!controller.signal.aborted) setDemo(settings)
      })
      .catch(() => {
        if (!controller.signal.aborted) setDemoError(true)
      })

    return () => controller.abort()
  }, [])

  async function handleRefreshDemo() {
    if (demo === null || refreshing) return

    setRefreshing(true)
    setRefreshMessage('')

    try {
      const result = await refreshDemoSales()
      setDemo({ ...demo, planning_date: result.planning_date })
      setSalesRevision((revision) => revision + 1)
      setRefreshMessage(
        result.added_sales === 0
          ? 'Os dados da demo já estão atualizados.'
          : `Dados da demo atualizados. Novos registros de vendas: ${result.added_sales}.`,
      )
    } catch {
      setRefreshMessage('Não foi possível atualizar os dados da demo. Tente novamente.')
    } finally {
      setRefreshing(false)
    }
  }

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

      <header
        className="app-header"
        onKeyDown={(event) => {
          if (event.key === 'Escape' && menuOpen) {
            setMenuOpen(false)
            menuToggle.current?.focus()
          }
        }}
      >
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

        <button
          ref={menuToggle}
          className="app-menu-toggle"
          type="button"
          aria-label="Menu de seções"
          aria-controls="app-navigation"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span className="app-menu-icon" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span className="app-menu-label">Menu</span>
        </button>

        <nav
          id="app-navigation"
          className="app-navigation"
          aria-label="Navegação principal"
          data-open={menuOpen}
        >
          {NAVIGATION.map((item) => (
            <a
              key={item.href}
              href={item.href}
              onClick={() => {
                if (menuOpen) {
                  setMenuOpen(false)
                  document.getElementById(item.href.slice(1))?.focus({ preventScroll: true })
                }
              }}
            >
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
            Decisões melhores, orientadas por dados.
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

          {demo?.refresh_enabled && demo.restaurant_id !== null && (
            <div className="demo-actions">
              <button type="button" onClick={handleRefreshDemo} disabled={refreshing}>
                {refreshing ? 'Atualizando dados…' : 'Atualizar dados da demo'}
              </button>
              <span role="status">{refreshMessage}</span>
            </div>
          )}
        </section>

        {demoError && <p role="alert">Não foi possível carregar a configuração da demo.</p>}
        {demo?.restaurant_id === null && (
          <p role="status">Execute a carga inicial da demo para habilitar estoque e assistente.</p>
        )}

        {demo && (
          <div id="previsao" className="dashboard-anchor" tabIndex={-1}>
            <ForecastDashboard
              defaultHorizon={demo.forecast_horizon}
              salesRevision={salesRevision}
            />
          </div>
        )}

        {demo && demo.restaurant_id !== null && (
          <>
            <div id="estoque" className="dashboard-anchor" tabIndex={-1}>
              <InventoryDashboard
                restaurantId={demo.restaurant_id}
                defaultStartDate={demo.planning_date}
                defaultHorizon={demo.inventory_horizon}
                salesRevision={salesRevision}
              />
            </div>

            <div id="assistente" className="dashboard-anchor" tabIndex={-1}>
              <AdvisorChat restaurantId={demo.restaurant_id} />
            </div>
          </>
        )}
      </main>

      <footer className="app-footer">
        <span>DemandPilot AI</span>
        <span>Machine Learning + IA Generativa</span>
      </footer>
    </div>
  )
}

export default App
