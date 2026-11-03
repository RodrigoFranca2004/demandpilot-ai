import { useEffect, useState } from 'react'

import {
  getInventoryAnalysis,
  type IngredientRisk,
  type InventoryAnalysis,
  type Quantity,
} from '../api/inventory'

const HORIZONS = [1, 7, 14, 30]

const quantityFormatter = new Intl.NumberFormat('pt-BR', {
  maximumFractionDigits: 3,
})

const dateFormatter = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
})

function getLocalToday(): string {
  const today = new Date()

  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

function formatDate(value: string): string {
  return dateFormatter.format(new Date(`${value}T00:00:00Z`))
}

function formatQuantity(value: Quantity): string {
  return quantityFormatter.format(Number(value))
}

function formatMethod(method: string): string {
  if (method === 'linear_regression') {
    return 'Regressão linear'
  }

  if (method === 'baseline') {
    return 'Média móvel'
  }

  return method.replaceAll('_', ' ')
}

function getCoverage(ingredient: IngredientRisk): number {
  const required = Number(ingredient.required_quantity)
  const available = Number(ingredient.available_quantity)

  if (required <= 0) {
    return 100
  }

  return Math.min(100, Math.max(0, (available / required) * 100))
}

function InventoryResults({
  report,
}: {
  report: InventoryAnalysis
}) {
  const riskyIngredients = report.ingredients.filter(
    (ingredient) => ingredient.at_risk,
  )

  const safeCount =
    report.ingredients.length - riskyIngredients.length

  const sortedIngredients = [...report.ingredients].sort(
    (first, second) =>
      Number(second.at_risk) - Number(first.at_risk) ||
      first.ingredient_name.localeCompare(second.ingredient_name),
  )

  const period =
    report.start_date === report.end_date
      ? formatDate(report.start_date)
      : `${formatDate(report.start_date)} – ${formatDate(report.end_date)}`

  return (
    <div className="inventory-results">
      <div className="inventory-summary-grid">
        <article className="inventory-summary-card">
          <span>Produtos analisados</span>
          <strong>{report.products.length}</strong>
          <small>Demanda estimada para o período</small>
        </article>

        <article className="inventory-summary-card inventory-summary-card--risk">
          <span>Ingredientes em risco</span>
          <strong>{riskyIngredients.length}</strong>
          <small>Reposição potencialmente necessária</small>
        </article>

        <article className="inventory-summary-card">
          <span>Ingredientes suficientes</span>
          <strong>{safeCount}</strong>
          <small>Estoque cobre a demanda estimada</small>
        </article>
      </div>

      <div className="inventory-period">
        <div>
          <span className="inventory-detail-label">
            Período de planejamento
          </span>
          <strong>{period}</strong>
        </div>

        <div>
          <span className="inventory-detail-label">
            Restaurante
          </span>
          <strong>#{report.restaurant_id}</strong>
        </div>
      </div>

      <section className="inventory-panel">
        <div className="inventory-panel-heading">
          <div>
            <h3>Risco de falta de ingredientes</h3>
            <p>
              Compare as quantidades necessárias com o estoque
              disponível.
            </p>
          </div>
        </div>

        {report.ingredients.length === 0 ? (
          <p className="inventory-empty">
            Nenhum ingrediente encontrado para esta análise.
          </p>
        ) : (
          <div className="inventory-table-wrapper">
            <table className="inventory-table">
              <thead>
                <tr>
                  <th scope="col">Ingrediente</th>
                  <th scope="col">Necessário</th>
                  <th scope="col">Disponível</th>
                  <th scope="col">Falta</th>
                  <th scope="col">Cobertura</th>
                  <th scope="col">Situação</th>
                </tr>
              </thead>

              <tbody>
                {sortedIngredients.map((ingredient) => {
                  const coverage = getCoverage(ingredient)

                  return (
                    <tr key={ingredient.ingredient_id}>
                      <td className="inventory-ingredient-name">
                        {ingredient.ingredient_name}
                      </td>

                      <td>
                        {formatQuantity(
                          ingredient.required_quantity,
                        )}{' '}
                        {ingredient.unit}
                      </td>

                      <td>
                        {formatQuantity(
                          ingredient.available_quantity,
                        )}{' '}
                        {ingredient.unit}
                      </td>

                      <td
                        className={
                          ingredient.at_risk
                            ? 'inventory-shortage'
                            : ''
                        }
                      >
                        {formatQuantity(
                          ingredient.shortage_quantity,
                        )}{' '}
                        {ingredient.unit}
                      </td>

                      <td>
                        <div className="inventory-coverage">
                          <div
                            className="inventory-coverage-track"
                            role="progressbar"
                            aria-label={`Cobertura de ${ingredient.ingredient_name}`}
                            aria-valuemin={0}
                            aria-valuemax={100}
                            aria-valuenow={Math.round(coverage)}
                          >
                            <div
                              className={`inventory-coverage-fill ${
                                ingredient.at_risk
                                  ? 'inventory-coverage-fill--risk'
                                  : ''
                              }`}
                              style={{
                                width: `${coverage}%`,
                              }}
                            />
                          </div>

                          <span>
                            {Math.round(coverage)}%
                          </span>
                        </div>
                      </td>

                      <td>
                        <span
                          className={`inventory-risk-label ${
                            ingredient.at_risk
                              ? 'inventory-risk-label--risk'
                              : 'inventory-risk-label--safe'
                          }`}
                        >
                          {ingredient.at_risk
                            ? 'Em risco'
                            : 'Suficiente'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="inventory-panel">
        <div className="inventory-panel-heading">
          <div>
            <h3>Planejamento de produção</h3>
            <p>
              Quantidades estimadas de produtos para o período
              selecionado.
            </p>
          </div>
        </div>

        {report.products.length === 0 ? (
          <p className="inventory-empty">
            Nenhuma previsão de produto disponível.
          </p>
        ) : (
          <div className="inventory-products-grid">
            {report.products.map((product) => (
              <article
                className="inventory-product-card"
                key={product.product_id}
              >
                <div className="inventory-product-heading">
                  <h4>{product.product_name}</h4>
                  <span>#{product.product_id}</span>
                </div>

                <div className="inventory-product-demand">
                  <strong>
                    {formatQuantity(product.predicted_units)}
                  </strong>
                  <span>unidades estimadas</span>
                </div>

                <div className="inventory-product-details">
                  <span>
                    Modelo: {formatMethod(product.selected_method)}
                  </span>
                  <span>
                    Histórico até: {formatDate(product.history_end_date)}
                  </span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <p className="inventory-disclaimer">
        As quantidades são estimativas baseadas no histórico de
        vendas, nas receitas cadastradas e no estoque disponível.
        Não representam pedidos de compra nem atualizam o
        inventário automaticamente.
      </p>
    </div>
  )
}

interface InventoryDashboardProps {
  restaurantId: number
}

export function InventoryDashboard({
  restaurantId,
}: InventoryDashboardProps) {
  const [startDate, setStartDate] = useState(getLocalToday)
  const [horizon, setHorizon] = useState(1)

  const [analysis, setAnalysis] = useState<
    InventoryAnalysis | null
  >(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadInventory() {
      setLoading(true)
      setError(null)
      setAnalysis(null)

      try {
        const result = await getInventoryAnalysis(
          restaurantId,
          startDate,
          horizon,
          controller.signal,
        )

        if (!controller.signal.aborted) {
          setAnalysis(result)
        }
      } catch (caughtError) {
        if (!controller.signal.aborted) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : 'Não foi possível carregar a análise de estoque.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadInventory()

    return () => controller.abort()
  }, [restaurantId, startDate, horizon])

  return (
    <section
      className="inventory-section"
      aria-labelledby="inventory-title"
    >
      <div className="section-heading">
        <div>
          <div className="eyebrow">INVENTORY INTELLIGENCE</div>
          <h2 id="inventory-title">Planejamento de estoque</h2>
        </div>

        <span className="section-note">Dados da API</span>
      </div>

      <div className="inventory-workspace">
        <div className="inventory-controls">
          <div className="inventory-control">
            <label htmlFor="inventory-start-date">
              Data inicial
            </label>

            <input
              id="inventory-start-date"
              type="date"
              min={getLocalToday()}
              value={startDate}
              onChange={(event) =>
                setStartDate(event.target.value)
              }
            />
          </div>

          <div className="inventory-control">
            <label htmlFor="inventory-horizon">
              Horizonte de planejamento
            </label>

            <select
              id="inventory-horizon"
              value={horizon}
              onChange={(event) =>
                setHorizon(Number(event.target.value))
              }
            >
              {HORIZONS.map((days) => (
                <option key={days} value={days}>
                  {days} {days === 1 ? 'dia' : 'dias'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading && (
          <p className="inventory-message" role="status">
            Calculando necessidades de estoque...
          </p>
        )}

        {!loading && error && (
          <p className="inventory-error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && analysis && (
          <InventoryResults report={analysis} />
        )}
      </div>
    </section>
  )
}