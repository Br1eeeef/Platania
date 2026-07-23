import { Play, RotateCcw, ShieldCheck } from 'lucide-react'
import { useMemo, useState, type FormEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Disclaimer } from '../components/Disclaimer'
import { api, ApiError } from '../services/api'
import type { BacktestRequest, StrategyId } from '../types'

const strategyDefinitions: Record<StrategyId, {
  name: string
  parameters: Array<{ key: string; label: string; defaultValue: number; min: number; max: number; step: number }>
}> = {
  trend_momentum: {
    name: '趋势动量',
    parameters: [
      { key: 'rsi_min', label: 'RSI 下限', defaultValue: 42, min: 0, max: 99, step: 1 },
      { key: 'rsi_max', label: 'RSI 上限', defaultValue: 72, min: 1, max: 100, step: 1 },
      { key: 'atr_stop', label: 'ATR 止损倍数', defaultValue: 3, min: .5, max: 10, step: .1 },
    ],
  },
  volume_breakout: {
    name: '放量突破',
    parameters: [
      { key: 'volume_ratio', label: '最低量比', defaultValue: 1.5, min: .5, max: 10, step: .1 },
      { key: 'atr_stop', label: 'ATR 止损倍数', defaultValue: 2.8, min: .5, max: 10, step: .1 },
    ],
  },
  mean_reversion: {
    name: '趋势内均值回归',
    parameters: [
      { key: 'rsi_entry', label: 'RSI 入场阈值', defaultValue: 32, min: 1, max: 50, step: 1 },
      { key: 'rsi_exit', label: 'RSI 退出阈值', defaultValue: 55, min: 30, max: 99, step: 1 },
      { key: 'max_holding_days', label: '最大持有交易日', defaultValue: 15, min: 1, max: 120, step: 1 },
    ],
  },
}

const parameterDefaults = (strategy: StrategyId) => Object.fromEntries(
  strategyDefinitions[strategy].parameters.map((item) => [item.key, item.defaultValue]),
)

export function BacktestWorkbenchPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const requestedStrategy = searchParams.get('strategy') as StrategyId | null
  const initialStrategy = requestedStrategy && requestedStrategy in strategyDefinitions ? requestedStrategy : 'trend_momentum'
  const [symbol, setSymbol] = useState((searchParams.get('symbol') || '600519.SH').toUpperCase())
  const [strategy, setStrategy] = useState<StrategyId>(initialStrategy)
  const [initialCash, setInitialCash] = useState(100000)
  const [maxPositionPct, setMaxPositionPct] = useState(90)
  const [commissionPct, setCommissionPct] = useState(.03)
  const [minimumCommission, setMinimumCommission] = useState(5)
  const [stampDutyPct, setStampDutyPct] = useState(.05)
  const [slippagePct, setSlippagePct] = useState(.05)
  const [benchmarkSymbol, setBenchmarkSymbol] = useState('000300.SH')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [strategyParameters, setStrategyParameters] = useState<Record<string, number>>(() => parameterDefaults(initialStrategy))
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const definition = useMemo(() => strategyDefinitions[strategy], [strategy])

  const changeStrategy = (value: StrategyId) => {
    setStrategy(value)
    setStrategyParameters(parameterDefaults(value))
  }

  const reset = () => {
    setInitialCash(100000); setMaxPositionPct(90); setCommissionPct(.03); setMinimumCommission(5)
    setStampDutyPct(.05); setSlippagePct(.05); setBenchmarkSymbol('000300.SH')
    setStartDate(''); setEndDate(''); setStrategyParameters(parameterDefaults(strategy)); setError('')
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    setRunning(true); setError('')
    const payload: BacktestRequest = {
      symbol: symbol.trim().toUpperCase(), strategy_id: strategy, initial_cash: initialCash,
      commission_rate: commissionPct / 100, minimum_commission: minimumCommission,
      stamp_duty_rate: stampDutyPct / 100, slippage_rate: slippagePct / 100,
      max_position: maxPositionPct / 100, benchmark_symbol: benchmarkSymbol.trim().toUpperCase(),
      strategy_parameters: strategyParameters,
      ...(startDate ? { start_date: startDate } : {}), ...(endDate ? { end_date: endDate } : {}),
    }
    try {
      const result = await api.backtest(payload)
      navigate(`/backtests/${result.id}`, { state: result })
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : '回测运行失败，请稍后重试')
    } finally { setRunning(false) }
  }

  return <div className="page backtest-workbench">
    <div className="page-header"><div><p className="eyebrow">BACKTEST LAB</p><h1>可配置回测工作台</h1><p>设置资金、交易成本、风险上限和白名单策略参数</p></div></div>
    <Disclaimer />
    <form onSubmit={(event) => void submit(event)}>
      <section className="config-panel"><div className="section-heading"><div><p className="eyebrow">UNIVERSE</p><h2>标的与策略</h2></div></div><div className="config-grid">
        <label>股票代码<input value={symbol} onChange={(event) => setSymbol(event.target.value)} pattern="[0-9]{6}\.(SH|SZ)" required placeholder="600519.SH" /></label>
        <label>平台策略<select value={strategy} onChange={(event) => changeStrategy(event.target.value as StrategyId)}>{Object.entries(strategyDefinitions).map(([id, item]) => <option key={id} value={id}>{item.name}</option>)}</select></label>
        <label>基准指数<input value={benchmarkSymbol} onChange={(event) => setBenchmarkSymbol(event.target.value)} pattern="[0-9]{6}\.(SH|SZ)" required /></label>
        <label>开始日期（可选）<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label>
        <label>结束日期（可选）<input type="date" value={endDate} min={startDate || undefined} onChange={(event) => setEndDate(event.target.value)} /></label>
      </div></section>
      <section className="config-panel"><div className="section-heading"><div><p className="eyebrow">CAPITAL & COSTS</p><h2>资金与交易成本</h2></div></div><div className="config-grid">
        <label>初始资金（元）<input type="number" min="10000" max="100000000" step="10000" value={initialCash} onChange={(event) => setInitialCash(Number(event.target.value))} required /></label>
        <label>最大仓位（%）<input type="number" min="1" max="100" step="1" value={maxPositionPct} onChange={(event) => setMaxPositionPct(Number(event.target.value))} required /></label>
        <label>佣金率（%）<input type="number" min="0" max="1" step="0.001" value={commissionPct} onChange={(event) => setCommissionPct(Number(event.target.value))} required /></label>
        <label>最低佣金（元）<input type="number" min="0" max="100" step="1" value={minimumCommission} onChange={(event) => setMinimumCommission(Number(event.target.value))} required /></label>
        <label>印花税率（%）<input type="number" min="0" max="1" step="0.001" value={stampDutyPct} onChange={(event) => setStampDutyPct(Number(event.target.value))} required /></label>
        <label>滑点（%）<input type="number" min="0" max="2" step="0.001" value={slippagePct} onChange={(event) => setSlippagePct(Number(event.target.value))} required /></label>
      </div></section>
      <section className="config-panel"><div className="section-heading"><div><p className="eyebrow">STRATEGY PARAMETERS</p><h2>{definition.name}参数</h2></div><span className="safe-config"><ShieldCheck size={15} />仅允许平台白名单参数</span></div><div className="config-grid">
        {definition.parameters.map((item) => <label key={item.key}>{item.label}<input type="number" min={item.min} max={item.max} step={item.step} value={strategyParameters[item.key]} onChange={(event) => setStrategyParameters((current) => ({ ...current, [item.key]: Number(event.target.value) }))} required /></label>)}
      </div></section>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="config-actions"><button type="button" className="button secondary" onClick={reset}><RotateCcw size={15} />恢复默认</button><button className="button primary" disabled={running}><Play size={15} />{running ? '正在运行回测' : '运行回测'}</button></div>
    </form>
  </div>
}
