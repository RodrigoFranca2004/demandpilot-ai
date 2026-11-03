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

const HORIZONS = [1, 7, 14, 30]

const numberFormatter = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 2,
})

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${value}T00:00:00Z`))
}

function formatMetric(value: number): string {
  return numberFormatter.format(value)
}

function formatMethod(method: string): string {
  if (method === 'linear_regression') {
    return 'Linear Regression'
  }

  if (method === 'baseline') {
    return 'Moving Average Baseline'
  }

  return method.replaceAll('_', ' ')
}

function ForecastResults({
  report,
}: {
  report: ForecastReport
}) {
  const chartData = report.forecast.map((point) => ({
    date: formatDate(point.sale_date),
    predicted: point.predicted_quantity,
  }))

  const selectedMethod = formatMethod(report.selected_method)

  return (
    <div className="forecast-results">
      <div className="forecast-summary">
        <div>
          <span className="forecast-detail-label">
            Selected model
          </span>
          <strong>{selectedMethod}</strong>
        </div>

        <div>
          <span className="forecast-detail-label">
            Last recorded sale
          </span>
          <strong>{report.history_end_date}</strong>
        </div>

        <div>
          <span className="forecast-detail-label">
            Forecast period
          </span>
          <strong>
            {report.forecast.length > 0
              ? `${formatDate(report.forecast[0].sale_date)} – ${formatDate(report.forecast[report.forecast.length - 1].sale_date)}`
              : 'No forecast available'}
          </strong>
        </div>
      </div>

      <div className="forecast-panel">
        <div className="forecast-panel-heading">
          <div>
            <h3>Predicted product demand</h3>
            <p>
              Estimated units per day based on historical sales.
            </p>
          </div>
          <span className="forecast-panel-unit">Units</span>
        </div>

        {chartData.length > 0 ? (
          <div
            className="forecast-chart"
            role="img"
            aria-label="Line chart showing predicted units for each forecast date"
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData}
                margin={{
                  top: 12,
                  right: 16,
                  left: -12,
                  bottom: 4,
                }}
              >
                <CartesianGrid
                  stroke="#263247"
                  strokeDasharray="3 5"
                  vertical={false}
                />

                <XAxis
                  dataKey="date"
                  stroke="#8795ab"
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                />

                <YAxis
                  stroke="#8795ab"
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                  width={55}
                  domain={[0, 'auto']}
                />

                <Tooltip
                  contentStyle={{
                    backgroundColor: '#182336',
                    border: '1px solid #334155',
                    borderRadius: 10,
                    color: '#e8edf5',
                  }}
                  labelStyle={{ color: '#e8edf5' }}
                  itemStyle={{ color: '#60e0b0' }}
                />

                <Line
                  type="monotone"
                  dataKey="predicted"
                  name="Predicted units"
                  stroke="#60e0b0"
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#60e0b0' }}
                  activeDot={{ r: 6 }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="forecast-message">
            No forecast observations were returned.
          </p>
        )}

        {report.forecast.length > 0 && (
          <div className="forecast-table-wrapper">
            <table className="forecast-table">
              <thead>
                <tr>
                  <th scope="col">Date</th>
                  <th scope="col">Predicted units</th>
                </tr>
              </thead>
              <tbody>
                {report.forecast.map((point) => (
                  <tr key={point.sale_date}>
                    <td>{point.sale_date}</td>
                    <td>
                      {formatMetric(point.predicted_quantity)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {report.baseline_metrics && report.regression_metrics && (
        <div className="forecast-metrics-section">
          <div className="forecast-panel-heading">
            <div>
              <h3>Model performance</h3>
              <p>
                Evaluation period: {report.evaluation_start_date} to{' '}
                {report.evaluation_end_date}
              </p>
            </div>
          </div>

          <div className="forecast-metrics-grid">
            <article
              className={`forecast-metric-card ${
                report.selected_method === 'baseline'
                  ? 'forecast-metric-card--selected'
                  : ''
              }`}
            >
              <div className="forecast-metric-header">
                <h4>Moving Average</h4>
                {report.selected_method === 'baseline' && (
                  <span className="forecast-selected-label">
                    Selected
                  </span>
                )}
              </div>

              <div className="forecast-metric-values">
                <div>
                  <span>MAE</span>
                  <strong>
                    {formatMetric(report.baseline_metrics.mae)}
                  </strong>
                </div>
                <div>
                  <span>WAPE</span>
                  <strong>
                    {formatMetric(report.baseline_metrics.wape)}%
                  </strong>
                </div>
              </div>
            </article>

            <article
              className={`forecast-metric-card ${
                report.selected_method === 'linear_regression'
                  ? 'forecast-metric-card--selected'
                  : ''
              }`}
            >
              <div className="forecast-metric-header">
                <h4>Linear Regression</h4>
                {report.selected_method === 'linear_regression' && (
                  <span className="forecast-selected-label">
                    Selected
                  </span>
                )}
              </div>

              <div className="forecast-metric-values">
                <div>
                  <span>MAE</span>
                  <strong>
                    {formatMetric(report.regression_metrics.mae)}
                  </strong>
                </div>
                <div>
                  <span>WAPE</span>
                  <strong>
                    {formatMetric(report.regression_metrics.wape)}%
                  </strong>
                </div>
              </div>
            </article>
          </div>
        </div>
      )}

      <p className="forecast-disclaimer">
        Forecasts are estimates, not guaranteed sales. Dates are based
        on the latest recorded sales, which may differ from today.
        Lower MAE and WAPE indicate better historical evaluation
        performance.
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

  const [loadingProducts, setLoadingProducts] = useState(true)
  const [productsError, setProductsError] = useState<string | null>(
    null,
  )

  const [forecast, setForecast] = useState<ForecastReport | null>(
    null,
  )
  const [loadingForecast, setLoadingForecast] = useState(false)
  const [forecastError, setForecastError] = useState<string | null>(
    null,
  )

  useEffect(() => {
    const controller = new AbortController()

    async function loadProducts() {
      try {
        const result = await getProducts(controller.signal)

        if (controller.signal.aborted) {
          return
        }

        setProducts(result)
        setSelectedProductId(result[0]?.id ?? null)
      } catch {
        if (!controller.signal.aborted) {
          setProductsError(
            'Unable to load products. Check the backend connection.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoadingProducts(false)
        }
      }
    }

    void loadProducts()

    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (selectedProductId === null) {
      return
    }

    const controller = new AbortController()

    async function loadForecast() {
      setLoadingForecast(true)
      setForecastError(null)
      setForecast(null)

      try {
        const result = await getProductForecast(
          selectedProductId!,
          horizon,
          controller.signal,
        )

        if (!controller.signal.aborted) {
          setForecast(result)
        }
      } catch {
        if (!controller.signal.aborted) {
          setForecastError(
            'Unable to load the forecast for this product.',
          )
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoadingForecast(false)
        }
      }
    }

    void loadForecast()

    return () => controller.abort()
  }, [selectedProductId, horizon])

  return (
    <section
      className="forecast-section"
      aria-labelledby="forecast-title"
    >
      <div className="section-heading">
        <div>
          <div className="eyebrow">DEMAND INTELLIGENCE</div>
          <h2 id="forecast-title">Demand forecasting</h2>
        </div>
        <span className="section-note">Live API data</span>
      </div>

      <div className="forecast-workspace">
        <div className="forecast-controls">
          <div className="forecast-control">
            <label htmlFor="forecast-product">
              Product
            </label>

            <select
              id="forecast-product"
              value={selectedProductId ?? ''}
              onChange={(event) =>
                setSelectedProductId(Number(event.target.value))
              }
              disabled={loadingProducts || products.length === 0}
            >
              {products.length === 0 && (
                <option value="">
                  {loadingProducts
                    ? 'Loading products...'
                    : 'No products available'}
                </option>
              )}

              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name}
                </option>
              ))}
            </select>
          </div>

          <div className="forecast-control">
            <label htmlFor="forecast-horizon">
              Forecast horizon
            </label>

            <select
              id="forecast-horizon"
              value={horizon}
              onChange={(event) =>
                setHorizon(Number(event.target.value))
              }
            >
              {HORIZONS.map((days) => (
                <option key={days} value={days}>
                  {days} {days === 1 ? 'day' : 'days'}
                </option>
              ))}
            </select>
          </div>
        </div>

        {productsError && (
          <p className="forecast-error" role="alert">
            {productsError}
          </p>
        )}

        {!loadingProducts &&
          !productsError &&
          products.length === 0 && (
            <p className="forecast-message">
              No products were found in the database. Seed the demo
              data to get started.
            </p>
          )}

        {loadingForecast && (
          <p className="forecast-message" role="status">
            Loading demand forecast...
          </p>
        )}

        {forecastError && (
          <p className="forecast-error" role="alert">
            {forecastError}
          </p>
        )}

        {!loadingForecast && forecast && (
          <ForecastResults report={forecast} />
        )}
      </div>
    </section>
  )
}