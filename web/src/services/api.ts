import { supabase } from './supabase'
import type { BacktestRequest, BacktestResult, Bar, DataMeta, FeedItem, IndicatorPoint, Instrument, SignalSnapshot, StrategyDescriptor, StrategyId, StrategySpec } from '../types'

export class ApiError extends Error {
  constructor(message: string, public status: number, public code = 'request_failed') {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const session = await supabase?.auth.getSession()
  const token = session?.data.session?.access_token
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), 15_000)
  try {
    const response = await fetch(path, {
      ...init,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init?.headers,
      },
    })
    if (!response.ok) {
      const payload = await response.json().catch(() => null)
      throw new ApiError(payload?.error?.message ?? payload?.detail ?? `请求失败 (${response.status})`, response.status, payload?.error?.code)
    }
    if (response.status === 204) return undefined as T
    return response.json() as Promise<T>
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === 'AbortError') throw new ApiError('请求超时，请稍后重试', 408, 'timeout')
    throw new ApiError(navigator.onLine ? '无法连接到服务' : '当前处于离线状态', 0, 'offline')
  } finally {
    window.clearTimeout(timer)
  }
}

export const api = {
  health: () => request<{ status: string; data_mode: string; ai_mode: string; auth_mode: string }>('/api/health'),
  marketStatus: () => request<Record<string, any>>('/api/market/status'),
  instruments: (page = 1, search = '') => request<{ items: Instrument[]; pagination: { page: number; page_size: number; total: number }; catalog_updated_at?: string; catalog_stale?: boolean }>(`/api/instruments?page=${page}&page_size=50&search=${encodeURIComponent(search)}`),
  bars: (symbol: string, period: '1d' | '1w' | '1m' | '5m' | '15m' | '30m' | '60m' = '1d') => request<{ instrument: Instrument; period: string; bars: Bar[]; meta: DataMeta }>(`/api/market/${symbol}/bars?period=${period}&limit=520`),
  indicators: (symbol: string, period: '1d' | '1m' | '5m' | '15m' | '30m' | '60m' = '1d') => request<{ instrument: Instrument; history: IndicatorPoint[]; meta: DataMeta }>(`/api/market/${symbol}/indicators?period=${period}&limit=520`),
  signals: (symbol: string, strategy: StrategyId) => request<{ symbol: string; signal: SignalSnapshot; history: Array<{ date: string; event: string; close: number }>; data_source: string; is_demo: boolean }>(`/api/market/${symbol}/signals?strategy_id=${strategy}`),
  strategies: () => request<{ items: StrategyDescriptor[] }>('/api/strategies'),
  backtest: (payload: BacktestRequest) => request<BacktestResult>('/api/backtests', { method: 'POST', body: JSON.stringify(payload) }),
  getBacktest: (id: string) => request<BacktestResult>(`/api/backtests/${id}`),
  aiGenerate: (prompt: string) => request<{ id: string; mode: 'mock' | 'deepseek'; spec: StrategySpec; readable_code: string; daily_used: number; daily_limit: number; disclaimer: string }>('/api/ai/strategy', { method: 'POST', body: JSON.stringify({ prompt }) }),
  aiBacktest: (symbol: string, spec: StrategySpec) => request<BacktestResult>('/api/ai/strategy/backtest', { method: 'POST', body: JSON.stringify({ symbol, spec }) }),
  feed: () => request<{ items: FeedItem[]; is_demo: boolean }>('/api/feed'),
  me: () => request<Record<string, any>>('/api/me'),
  watchlist: () => request<Array<{ symbol: string; added_at: string }>>('/api/watchlist'),
  addWatchlist: (symbol: string) => request('/api/watchlist', { method: 'POST', body: JSON.stringify({ symbol }) }),
  removeWatchlist: (symbol: string) => request(`/api/watchlist/${symbol}`, { method: 'DELETE' }),
  adminDashboard: () => request<{ total: number; active: number; expiring_soon: number; suspended: number }>('/api/admin'),
  adminMembers: () => request<Array<Record<string, any>>>('/api/admin/members'),
  adminInvite: (payload: Record<string, any>) => request('/api/admin/members', { method: 'POST', body: JSON.stringify(payload) }),
  adminUpdate: (userId: string, payload: Record<string, any>) => request(`/api/admin/members/${userId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  adminUsage: () => request<{ members: Array<Record<string, any>> }>('/api/admin/usage'),
  adminAudit: () => request<Array<Record<string, any>>>('/api/admin/audit-log'),
}
