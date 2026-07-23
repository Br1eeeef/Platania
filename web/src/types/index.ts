export type DataKind = 'live' | 'demo'
export type StrategyId = 'trend_momentum' | 'volume_breakout' | 'mean_reversion'

export interface Instrument {
  symbol: string
  code: string
  name: string
  exchange: 'SH' | 'SZ'
  market: string
  sector: string
  status: string
}

export interface Bar {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  suspended: boolean
  adjustment: string
}

export interface DataMeta {
  provider: string
  kind: DataKind
  updated_at: string
  adjustment: string
  timeframe: string
  is_stale: boolean
  warnings: string[]
}

export interface IndicatorPoint {
  date: string
  ma5: number | null
  ma20: number | null
  ma60: number | null
  ma120: number | null
  ema12: number | null
  ema26: number | null
  macd: number | null
  macd_signal: number | null
  macd_hist: number | null
  rsi14: number | null
  bollinger_upper: number | null
  bollinger_lower: number | null
  atr14: number | null
  momentum60: number | null
  volume_ratio: number | null
}

export interface SignalSnapshot {
  strategy_id: StrategyId
  state: '观察' | '买入候选' | '持有' | '减仓' | '退出'
  generated_at: string
  reasons: string[]
  invalidation: string
  risk_level: '低' | '中' | '高'
  score: number
  values: Record<string, number | null>
}

export interface StrategyDescriptor {
  id: StrategyId
  name: string
  summary: string
  parameters: Record<string, number>
}

export interface BacktestResult {
  id: string
  symbol: string
  strategy_id: StrategyId | 'ai_generated'
  metrics: {
    total_return: number
    annualized_return: number
    benchmark_return: number
    max_drawdown: number
    sharpe_ratio: number
    win_rate: number
    profit_factor: number | null
    trade_count: number
    average_holding_days: number
  }
  equity_curve: Array<{ date: string; value: number }>
  drawdown_curve: Array<{ date: string; value: number }>
  trades: Array<{
    entry_date: string
    exit_date: string
    entry_price: number
    exit_price: number
    quantity: number
    holding_days: number
    pnl: number
    return_rate: number
    costs: number
  }>
  parameters: Record<string, unknown>
  data_range: { start: string; end: string }
  data_source: string
  is_demo: boolean
}

export interface BacktestRequest {
  symbol: string
  strategy_id: StrategyId
  initial_cash: number
  commission_rate: number
  minimum_commission: number
  stamp_duty_rate: number
  slippage_rate: number
  max_position: number
  benchmark_symbol: string
  start_date?: string
  end_date?: string
  strategy_parameters: Record<string, number>
}

export interface StrategySpec {
  version: '1.0'
  name: string
  market: 'A股'
  universe: string[]
  exclusions: string[]
  filters: Condition[]
  entry_conditions: Condition[]
  exit_conditions: Condition[]
  risk: { stop_loss_pct: number; take_profit_pct: number | null; max_position: number }
  rebalance_frequency: string
  costs: { commission_rate: number; stamp_duty_rate: number; slippage_rate: number }
  benchmark: string
  parameter_notes: Record<string, string>
}

export interface Condition {
  left: { name: string; period: number | null }
  operator: string
  right: { name: string; period: number | null } | number
}

export interface FeedItem {
  id: string
  kind: string
  author_name: string
  title: string
  excerpt: string
  symbol?: string
  strategy_id?: string
  created_at: string
  likes: number
  comments: number
  is_demo: boolean
}
