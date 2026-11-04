import { useEffect, useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  getProductForecast,
  getProducts,
  type ForecastReport,
  type Product,
} from '../api/forecasting'
import './ForecastDashboard.css'

const HORIZONS = [1, 7, 14, 30]

const numberFormatter = new Intl.NumberFormat('pt-BR', {
  maximumFractionDigits: 1,
})

const metricFormatter = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

function formatDate(
  value: string,
  options: Intl.DateTimeFormatOptions = {},
): string {
  const date = new Date(`${value}T00:00:00Z`)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
    ...options,
  }).format(date)
}

function formatMethod(method: string): string {
  if (method === 'linear_regression') {
    return 'Regressão linear'
  }

  if (method === 'baseline') {
    return 'Modelo de referência'
  }

  return method.replaceAll('_', ' ')
}

function ForecastResults({
  report,
  productName,
}: {
  report: ForecastReport
  productName: string
}) {
  if (
    !Array.isArray(report.forecast) ||
    !report.baseline_metrics ||
    !report.regression_metrics
  ) {
    return (
      <p className="dashboard-feedback dashboard-feedback--error" role="alert">
        Os dados de previsão recebidos estão incompletos.
      </p>
    )
  }

  const chartData = report.forecast.map((point) => ({
    date: formatDate(point.sale_date, {
      year: undefined,
    }),
    quantity: Number(point.predicted_quantity.toFixed(1)),
  }))

  const metrics = [
    {
      id: 'baseline',
      name: 'Modelo de referência',
      values: report.baseline_metrics,
    },
    {
      id: 'linear_regression',
      name: 'Regressão linear',
      values: report.regression_metrics,
    },
  ]

  return (
    <div className="forecast-ui-results">
      <div className="forecast-ui-summary">
        <article className="forecast-ui-summary-card">
          <span>Modelo selecionado</span>
          <strong>
            {formatMethod(report.selected_method)}
          </strong>
          <small>
            Modelo utilizado nas previsões apresentadas
          </small>
        </article>

        <article className="forecast-ui-summary-card">
          <span>Última venda registrada</span>
          <strong>
            {formatDate(report.history_end_date)}
          </strong>
          <small>
            Referência do histórico de vendas
          </small>
        </article>

        <article className="forecast-ui-summary-card">
          <span>Horizonte da previsão</span>
          <strong>
            {report.forecast.length}{' '}
            {report.forecast.length === 1 ? 'dia' : 'dias'}
          </strong>
          <small>
            Quantidades estimadas para {productName}
          </small>
        </article>
      </div>

      <section
        className="forecast-ui-panel"
        aria-labelledby="forecast-chart-title"
      >
        <div className="forecast-ui-panel-heading">
          <h3 id="forecast-chart-title">
            Demanda prevista
          </h3>
          <p>
            Estimativa de unidades por dia para {productName}.
          </p>
        </div>

        {chartData.length === 0 ? (
          <p className="dashboard-feedback">
            Nenhuma previsão disponível para este período.
          </p>
        ) : (
          <div
            className="forecast-ui-chart"
            role="img"
            aria-label={`Gráfico da demanda prevista de ${productName}. Os valores detalhados estão na tabela abaixo.`}
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={chartData}
                margin={{
                  top: 12,
                  right: 12,
                  left: -12,
                  bottom: 8,
                }}
              >
                <CartesianGrid
                  stroke="#34435b"
                  strokeDasharray="4 4"
                  vertical={false}
                />

                <XAxis
                  dataKey="date"
                  stroke="#8795ab"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  minTickGap={20}
                />

                <YAxis
                  stroke="#8795ab"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  domain={[0, 'auto']}
                  width={45}
                />

                <Tooltip
                  contentStyle={{
                    backgroundColor: '#192438',
                    border: '1px solid #34435b',
                    borderRadius: '10px',
                    color: '#e8edf5',
                  }}
                />

                <Line
                  type="monotone"
                  dataKey="quantity"
                  name="Unidades previstas"
                  stroke="#60e0b0"
                  strokeWidth={3}
                  dot={chartData.length <= 7}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section
        className="forecast-ui-panel"
        aria-labelledby="forecast-metrics-title"
      >
        <div className="forecast-ui-panel-heading">
          <h3 id="forecast-metrics-title">
            Desempenho dos modelos
          </h3>
          <p>
            Avaliação entre {formatDate(report.evaluation_start_date)}
            {' '}e {formatDate(report.evaluation_end_date)}.
            Valores menores indicam erros menores.
          </p>
        </div>

        <div className="forecast-ui-metrics">
          {metrics.map((model) => {
            const selected =
              report.selected_method === model.id

            return (
              <article
                key={model.id}
                className={`forecast-ui-metric-card ${
                  selected
                    ? 'forecast-ui-metric-card--selected'
                    : ''
                }`}
              >
                <div className="forecast-ui-metric-heading">
                  <h4>{model.name}</h4>

                  {selected && (
                    <span className="forecast-ui-selected-label">
                      Selecionado
                    </span>
                  )}
                </div>

                <div className="forecast-ui-metric-values">
                  <div>
                    <span>MAE</span>
                    <strong>
                      {metricFormatter.format(model.values.mae)}
                    </strong>
                  </div>

                  <div>
                    <span>WAPE</span>
                    <strong>
                      {metricFormatter.format(model.values.wape)}%
                    </strong>
                  </div>
                </div>
              </article>
            )
          })}
        </div>

        <p className="forecast-ui-hint">
          MAE é o erro médio absoluto, em unidades. WAPE é o
          erro absoluto percentual ponderado.
        </p>
      </section>

      <section
        className="forecast-ui-panel"
        aria-labelledby="forecast-table-title"
      >
        <div className="forecast-ui-panel-heading">
          <h3 id="forecast-table-title">
            Previsões por dia
          </h3>
          <p>
            Valores calculados pelo modelo selecionado.
          </p>
        </div>

        <div className="forecast-ui-table-wrapper">
          <table className="forecast-ui-table">
            <thead>
              <tr>
                <th scope="col">Data</th>
                <th scope="col">Demanda prevista</th>
                <th scope="col">Modelo</th>
              </tr>
            </thead>

            <tbody>
              {report.forecast.map((point) => (
                <tr key={point.sale_date}>
                  <td>
                    {formatDate(point.sale_date)}
                  </td>

                  <td>
                    <strong>
                      {numberFormatter.format(
                        point.predicted_quantity,
                      )}
                    </strong>
                    {' '}unidades
                  </td>

                  <td>
                    {formatMethod(report.selected_method)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <p className="forecast-ui-disclaimer">
        As previsões começam após a última data disponível
        no histórico de vendas. Os resultados são estimativas
        calculadas pelo modelo e não representam vendas
        realizadas ou dados atualizados em tempo real.
      </p>
    </div>
  )
}

export function ForecastDashboard() {
  const [products, setProducts] = useState<Product[]>([])
  const [selectedProductId, setSelectedProductId] = useState<
    number | null
  >(null)
  const [horizon, setHorizon] = useState(7)

  const [productsLoading, setProductsLoading] = useState(true)
  const [productsError, setProductsError] = useState<
    string | null
  >(null)

  const [report, setReport] = useState<ForecastReport | null>(
    null,
  )
  const [forecastLoading, setForecastLoading] = useState(false)
  const [forecastError, setForecastError] = useState<
    string | null
  >(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadProducts() {
      setProductsLoading(true)
      setProductsError(null)

      try {
        const result = await getProducts(controller.signal)

        if (!Array.isArray(result)) {
          throw new Error(
            'Formato inesperado na lista de produtos.',
          )
        }

        if (!controller.signal.aborted) {
          setProducts(result)
          setSelectedProductId(result[0]?.id ?? null)
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setProductsError(
            error instanceof Error
              ? error.message
              : 'Não foi possível carregar os produtos.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setProductsLoading(false)
        }
      }
    }

    void loadProducts()

    return () => controller.abort()
  }, [])

  useEffect(() => {
    const controller = new AbortController()

    async function loadForecast() {
      const productId = selectedProductId

      if (productId === null) {
        return
      }

      setForecastLoading(true)
      setForecastError(null)
      setReport(null)

      try {
        const result = await getProductForecast(
          productId,
          horizon,
          controller.signal,
        )

        if (!controller.signal.aborted) {
          setReport(result)
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setForecastError(
            error instanceof Error
              ? error.message
              : 'Não foi possível carregar a previsão.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setForecastLoading(false)
        }
      }
    }

    void loadForecast()

    return () => controller.abort()
  }, [selectedProductId, horizon])

  const selectedProduct = products.find(
    (product) => product.id === selectedProductId,
  )

  return (
    <section
      className="forecast-section"
      aria-labelledby="forecast-title"
    >
      <div className="section-heading">
        <div>
          <div className="eyebrow">
            MACHINE LEARNING
          </div>
          <h2 id="forecast-title">
            Previsão de demanda
          </h2>
        </div>

        <span className="section-note">
          Dados da API
        </span>
      </div>

      <div className="forecast-ui">
        <div className="forecast-ui-controls">
          <div className="forecast-ui-control">
            <label htmlFor="forecast-product">
              Produto
            </label>

            <select
              id="forecast-product"
              value={selectedProductId ?? ''}
              onChange={(event) =>
                setSelectedProductId(
                  Number(event.target.value),
                )
              }
              disabled={
                productsLoading ||
                products.length === 0
              }
            >
              {products.length === 0 && (
                <option value="">
                  Nenhum produto disponível
                </option>
              )}

              {products.map((product) => (
                <option
                  key={product.id}
                  value={product.id}
                >
                  {product.name}
                </option>
              ))}
            </select>
          </div>

          <div className="forecast-ui-control">
            <label htmlFor="forecast-horizon">
              Horizonte da previsão
            </label>

            <select
              id="forecast-horizon"
              value={horizon}
              onChange={(event) =>
                setHorizon(Number(event.target.value))
              }
              disabled={productsLoading}
            >
              {HORIZONS.map((days) => (
                <option key={days} value={days}>
                  {days} {days === 1 ? 'dia' : 'dias'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {productsLoading && (
          <p className="dashboard-feedback" role="status">
            Carregando produtos...
          </p>
        )}

        {!productsLoading && productsError && (
          <p
            className="dashboard-feedback dashboard-feedback--error"
            role="alert"
          >
            {productsError}
          </p>
        )}

        {!productsLoading &&
          !productsError &&
          products.length === 0 && (
            <p className="dashboard-feedback">
              Nenhum produto cadastrado.
            </p>
          )}

        {!productsLoading &&
          !productsError &&
          products.length > 0 && (
            <>
              {forecastLoading && (
                <p
                  className="dashboard-feedback"
                  role="status"
                >
                  Calculando previsão de demanda...
                </p>
              )}

              {!forecastLoading && forecastError && (
                <p
                  className="dashboard-feedback dashboard-feedback--error"
                  role="alert"
                >
                  {forecastError}
                </p>
              )}

              {!forecastLoading &&
                !forecastError &&
                report &&
                selectedProduct && (
                  <ForecastResults
                    report={report}
                    productName={selectedProduct.name}
                  />
                )}
            </>
          )}
      </div>
    </section>
  )
}