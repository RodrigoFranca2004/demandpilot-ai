import { useEffect, useState } from 'react'

import { ForecastDashboard } from './components/ForecastDashboard'
import './App.css'

type ApiStatus = 'checking' | 'online' | 'offline'

const upcomingFeatures = [
  {
    number: '02',
    title: 'Inventory Planning',
    description:
      'Identify ingredient requirements and potential stock shortages.',
  },
  {
    number: '03',
    title: 'AI Advisor',
    description:
      'Ask questions about restaurant operations using Gemini.',
  },
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
    checking: 'Checking API connection',
    online: 'API connected',
    offline: 'API unavailable',
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

        <section
          className="features-section"
          aria-labelledby="features-title"
        >
          <div className="section-heading">
            <div>
              <div className="eyebrow">COMING NEXT</div>
              <h2 id="features-title">More capabilities</h2>
            </div>
          </div>

          <div className="feature-grid">
            {upcomingFeatures.map((feature) => (
              <article
                className="feature-card"
                key={feature.number}
              >
                <div className="feature-card-top">
                  <span className="feature-number">
                    {feature.number}
                  </span>
                  <span className="feature-state">
                    Coming next
                  </span>
                </div>

                <div>
                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <span>DemandPilot AI</span>
        <span>Machine Learning + Generative AI</span>
      </footer>
    </div>
  )
}

export default App