export interface Product {
  id: number
  name: string
}

export interface ForecastMetrics {
  mae: number
  wape: number
}

export interface ForecastPoint {
  sale_date: string
  predicted_quantity: number
}

interface ForecastResponse {
  product_id: number
  selected_method: string
  history_end_date: string
  forecast: ForecastPoint[]
}

interface ForecastMetricsResponse {
  product_id: number
  selected_method: string
  evaluation_start_date: string
  evaluation_end_date: string
  baseline_metrics: ForecastMetrics
  regression_metrics: ForecastMetrics
}

export interface ForecastReport
  extends ForecastResponse, ForecastMetricsResponse {}

async function getJson<T>(
  path: string,
  signal: AbortSignal,
): Promise<T> {
  const response = await fetch(`/api${path}`, { signal })

  if (!response.ok) {
    throw new Error(
      `API request failed with status ${response.status}`,
    )
  }

  return (await response.json()) as T
}

export function getProducts(
  signal: AbortSignal,
): Promise<Product[]> {
  return getJson<Product[]>('/products', signal)
}

export async function getProductForecast(
  productId: number,
  horizon: number,
  signal: AbortSignal,
): Promise<ForecastReport> {
  const [forecast, metrics] = await Promise.all([
    getJson<ForecastResponse>(
      `/products/${productId}/forecast?horizon=${horizon}`,
      signal,
    ),
    getJson<ForecastMetricsResponse>(
      `/products/${productId}/forecast/metrics`,
      signal,
    ),
  ])

  if (
    forecast.product_id !== metrics.product_id ||
    forecast.selected_method !== metrics.selected_method
  ) {
    throw new Error('Forecast and metrics data are inconsistent')
  }

  return {
    ...forecast,
    ...metrics,
  }
}