import type { Analysis, Overview, Stock, Strategy, StrategyId } from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)
  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? `请求失败 (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const api = {
  catalog: () => request<{ stocks: Stock[]; strategies: Strategy[] }>('/api/stocks'),
  overview: () => request<Overview>('/api/overview'),
  analysis: (symbol: string, strategy: StrategyId) =>
    request<Analysis>(`/api/stocks/${symbol}/analysis?strategy=${strategy}`),
  refresh: (symbol: string) =>
    request<{ data_meta: Analysis['data_meta'] }>(`/api/stocks/${symbol}/refresh?source=auto`, {
      method: 'POST',
    }),
}

