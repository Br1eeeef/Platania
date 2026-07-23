import { Plus, RefreshCw, SlidersHorizontal } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { DataBadge } from '../components/DataBadge'
import { Disclaimer } from '../components/Disclaimer'
import { ErrorState, LoadingState } from '../components/PageState'
import { PriceChart, type Overlay } from '../components/PriceChart'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'
import type { StrategyId } from '../types'
import { number, percent, tone } from '../utils/format'

const strategies: Array<{ id: StrategyId; name: string }> = [
  { id: 'trend_momentum', name: '趋势动量' }, { id: 'volume_breakout', name: '放量突破' }, { id: 'mean_reversion', name: '均值回归' },
]

export function StockPage() {
  const { symbol = '600519.SH' } = useParams()
  const navigate = useNavigate()
  const [period, setPeriod] = useState<'1d' | '1w' | '1m' | '5m' | '15m' | '30m' | '60m'>('1d')
  const [range, setRange] = useState(260)
  const [strategy, setStrategy] = useState<StrategyId>('trend_momentum')
  const [overlays, setOverlays] = useState<Set<Overlay>>(new Set(['ma20', 'ma60', 'ma120']))
  const indicatorPeriod = period === '1w' ? '1d' : period
  const { data, loading, error, retry } = useAsync(() => Promise.all([api.bars(symbol, period), api.indicators(symbol, indicatorPeriod), api.signals(symbol, strategy)]), [symbol, period, strategy])
  const visible = useMemo(() => data ? { bars: data[0].bars.slice(-range), indicators: data[1].history.slice(-range) } : null, [data, range])
  if (loading && !data) return <LoadingState />
  if (error || !data || !visible) return <ErrorState error={error ?? new Error('无行情数据')} retry={retry} />
  const [barsResponse, indicatorResponse, signalResponse] = data
  const latest = barsResponse.bars.at(-1)!
  const previous = barsResponse.bars.at(-2)!
  const change = latest.close / previous.close - 1
  const indicators = indicatorResponse.history.at(-1)!
  const toggleOverlay = (overlay: Overlay) => setOverlays((current) => {
    const next = new Set(current)
    if (next.has(overlay)) next.delete(overlay)
    else next.add(overlay)
    return next
  })
  const configureBacktest = () => navigate(`/backtests/new?symbol=${encodeURIComponent(symbol)}&strategy=${strategy}`)
  return <div className="stock-page">
    <header className="stock-header"><div><div className="title-line"><h1>{barsResponse.instrument.name}</h1><span>{barsResponse.instrument.symbol}</span><span>{barsResponse.instrument.sector}</span></div><div className="quote"><strong>{number(latest.close)}</strong><span className={tone(change)}>{percent(change)}</span><small>{latest.date} 收盘</small></div></div><DataBadge meta={barsResponse.meta} /></header>
    <Disclaimer compact />
    <div className="stock-layout">
      <aside className="stock-left"><h2>策略切换</h2>{strategies.map((item) => <button key={item.id} onClick={() => setStrategy(item.id)} className={strategy === item.id ? 'active' : ''}>{item.name}</button>)}<div className="watch-action"><button className="button secondary" onClick={() => void api.addWatchlist(symbol)}><Plus size={15} />加入自选</button></div></aside>
      <section className="chart-workspace">
        <div className="chart-toolbar"><div className="segmented"><button className={period === '1d' ? 'active' : ''} onClick={() => setPeriod('1d')}>日K</button><button className={period === '1w' ? 'active' : ''} onClick={() => setPeriod('1w')}>周K</button><button className={period === '1m' ? 'active' : ''} onClick={() => setPeriod('1m')}>1分</button><button className={period === '5m' ? 'active' : ''} onClick={() => setPeriod('5m')}>5分</button><button className={period === '15m' ? 'active' : ''} onClick={() => setPeriod('15m')}>15分</button><button className={period === '30m' ? 'active' : ''} onClick={() => setPeriod('30m')}>30分</button><button className={period === '60m' ? 'active' : ''} onClick={() => setPeriod('60m')}>60分</button></div><div className="segmented"><button className={range === 120 ? 'active' : ''} onClick={() => setRange(120)}>短期</button><button className={range === 260 ? 'active' : ''} onClick={() => setRange(260)}>中期</button><button className={range === 520 ? 'active' : ''} onClick={() => setRange(520)}>全部</button></div><button className="icon-button" onClick={retry} aria-label="重新加载"><RefreshCw size={16} /></button></div>
        <div className="indicator-toggles" aria-label="图表指标">{(['ma5','ma20','ma60','ma120','ema','bollinger'] as Overlay[]).map((item) => <label key={item}><input type="checkbox" checked={overlays.has(item)} onChange={() => toggleOverlay(item)} />{item.toUpperCase()}</label>)}</div>
        <PriceChart bars={visible.bars} indicators={visible.indicators} overlays={overlays} signals={signalResponse.history} />
        <div className="technical-strip"><div><span>MACD</span><strong className={tone(indicators.macd_hist ?? 0)}>{number(indicators.macd_hist ?? 0, 3)}</strong></div><div><span>RSI 14</span><strong>{number(indicators.rsi14 ?? 0, 1)}</strong></div><div><span>ATR 14</span><strong>{number(indicators.atr14 ?? 0, 2)}</strong></div><div><span>60日动量</span><strong className={tone(indicators.momentum60 ?? 0)}>{percent(indicators.momentum60 ?? 0)}</strong></div><div><span>量比</span><strong>{number(indicators.volume_ratio ?? 0, 2)}</strong></div></div>
      </section>
      <aside className="signal-panel"><div className="signal-score"><span>当前策略信号</span><strong>{signalResponse.signal.score}</strong><small>/ 100</small></div><span className={`signal-state ${signalResponse.signal.state === '持有' ? 'active' : ''}`}>{signalResponse.signal.state}</span><dl><div><dt>产生日期</dt><dd>{signalResponse.signal.generated_at}</dd></div><div><dt>风险等级</dt><dd>{signalResponse.signal.risk_level}</dd></div></dl><h3>触发规则</h3><ul>{signalResponse.signal.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul><h3>失效条件</h3><p>{signalResponse.signal.invalidation}</p><button className="button primary full" onClick={configureBacktest}><SlidersHorizontal size={15} />配置并运行回测</button></aside>
    </div>
  </div>
}
