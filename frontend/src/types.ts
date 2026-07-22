export type StrategyId = 'trend' | 'breakout' | 'mean_reversion'

export interface Stock {
  symbol: string
  name: string
  exchange: string
  sector: string
}

export interface Candidate extends Stock {
  close: number
  change: number
  score: number
  rating: string
  position: string
  source: string
}

export interface Strategy {
  id: StrategyId
  name: string
  description: string
}

export interface Bar {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  ma20: number | null
  ma60: number | null
  ma120: number | null
  rsi14: number | null
  atr14: number | null
  bollinger_upper: number | null
  bollinger_lower: number | null
  volume_ratio: number | null
  entry: boolean
  exit: boolean
  position: number
}

export interface Backtest {
  initial_cash: number
  final_equity: number
  total_return: number
  annualized_return: number
  benchmark_return: number
  max_drawdown: number
  sharpe: number
  trade_count: number
  win_rate: number
  equity_curve: Array<{ date: string; equity: number }>
  trades: Array<{
    entry_date: string
    exit_date: string
    entry_price: number
    exit_price: number
    quantity: number
    return: number
    pnl: number
  }>
  assumptions: Record<string, string | number>
}

export interface Analysis {
  stock: Stock
  strategy: Strategy
  quote: { date: string; close: number; change: number; volume: number }
  signal: {
    score: number
    rating: string
    position: string
    momentum_60d: number
    rsi14: number | null
    volume_ratio: number | null
    atr_ratio: number
  }
  backtest: Backtest
  bars: Bar[]
  data_meta: { source: string; updated_at: string; is_demo: boolean }
}

export interface Overview {
  market: string
  stock_count: number
  advancers: number
  decliners: number
  average_change: number
  candidates: Candidate[]
}

