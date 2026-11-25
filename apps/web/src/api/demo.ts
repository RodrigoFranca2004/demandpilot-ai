export interface DemoSettings {
  restaurant_id: number | null
  planning_date: string
  forecast_horizon: number
  inventory_horizon: number
  refresh_enabled: boolean
}

interface DemoRefreshResult {
  planning_date: string
  added_sales: number
}

export async function getDemoSettings(
  signal: AbortSignal,
): Promise<DemoSettings> {
  const response = await fetch('/api/demo', { signal })

  if (!response.ok) {
    throw new Error('Não foi possível carregar a configuração da demo.')
  }

  return response.json()
}

export async function refreshDemoSales(): Promise<DemoRefreshResult> {
  const response = await fetch('/api/demo/sales/refresh', { method: 'POST' })

  if (!response.ok) {
    throw new Error('Não foi possível atualizar os dados da demo.')
  }

  return response.json()
}
