export type Quantity = number | string

export interface ProductDemand {
  product_id: number
  product_name: string
  predicted_units: number
  selected_method: string
  history_end_date: string
}

export interface IngredientRisk {
  ingredient_id: number
  ingredient_name: string
  unit: string
  required_quantity: Quantity
  available_quantity: Quantity
  shortage_quantity: Quantity
  at_risk: boolean
}

export interface InventoryAnalysis {
  restaurant_id: number
  start_date: string
  end_date: string
  products: ProductDemand[]
  ingredients: IngredientRisk[]
}

function isInventoryAnalysis(
  value: unknown,
): value is InventoryAnalysis {
  if (typeof value !== 'object' || value === null) {
    return false
  }

  const data = value as Record<string, unknown>

  return (
    typeof data.restaurant_id === 'number' &&
    typeof data.start_date === 'string' &&
    typeof data.end_date === 'string' &&
    Array.isArray(data.products) &&
    data.products.every(
      (product: unknown) =>
        typeof product === 'object' &&
        product !== null &&
        typeof (product as ProductDemand).product_name === 'string' &&
        typeof (product as ProductDemand).predicted_units === 'number',
    ) &&
    Array.isArray(data.ingredients) &&
    data.ingredients.every(
      (ingredient: unknown) =>
        typeof ingredient === 'object' &&
        ingredient !== null &&
        typeof (ingredient as IngredientRisk).ingredient_name ===
          'string' &&
        typeof (ingredient as IngredientRisk).unit === 'string' &&
        typeof (ingredient as IngredientRisk).at_risk === 'boolean' &&
        Number.isFinite(
          Number(
            (ingredient as IngredientRisk).required_quantity,
          ),
        ) &&
        Number.isFinite(
          Number(
            (ingredient as IngredientRisk).available_quantity,
          ),
        ) &&
        Number.isFinite(
          Number(
            (ingredient as IngredientRisk).shortage_quantity,
          ),
        ),
    )
  )
}

export async function getInventoryAnalysis(
  restaurantId: number,
  startDate: string,
  horizon: number,
  signal: AbortSignal,
): Promise<InventoryAnalysis> {
  const params = new URLSearchParams({
    start_date: startDate,
    horizon: String(horizon),
  })

  const response = await fetch(
    `/api/restaurants/${restaurantId}/inventory/analysis?${params}`,
    { signal },
  )

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Restaurante não encontrado.')
    }

    if (response.status === 422) {
      throw new Error(
        'Não foi possível analisar esse período. Verifique a data inicial e o histórico de vendas.',
      )
    }

    throw new Error(
      `Falha ao consultar o estoque (HTTP ${response.status}).`,
    )
  }

  const data: unknown = await response.json()

  if (!isInventoryAnalysis(data)) {
    throw new Error('Formato inesperado na resposta de estoque.')
  }

  return data
}