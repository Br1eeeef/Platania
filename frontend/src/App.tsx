import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  BarChart3,
  Database,
  LineChart,
  LoaderCircle,
  RefreshCw,
  Search,
  ShieldCheck,
} from 'lucide-react'
import { api } from './api'
import { BacktestPanel } from './components/BacktestPanel'
import { CandidateTable } from './components/CandidateTable'
import { PriceChart } from './components/PriceChart'
import type { Analysis, Overview, Stock, Strategy, StrategyId } from './types'
import { formatPercent, priceClass } from './utils'

function App() {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [overview, setOverview] = useState<Overview | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [symbol, setSymbol] = useState('600519')
  const [strategy, setStrategy] = useState<StrategyId>('trend')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    Promise.all([api.catalog(), api.overview()])
      .then(([catalog, market]) => {
        if (!active) return
        setStocks(catalog.stocks)
        setStrategies(catalog.strategies)
        setOverview(market)
      })
      .catch((reason: Error) => active && setError(reason.message))
    return () => { active = false }
  }, [])

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    api.analysis(symbol, strategy)
      .then((result) => active && setAnalysis(result))
      .catch((reason: Error) => active && setError(reason.message))
      .finally(() => active && setLoading(false))
    return () => { active = false }
  }, [symbol, strategy])

  const refresh = useCallback(async () => {
    setRefreshing(true)
    setError(null)
    try {
      await api.refresh(symbol)
      const [nextAnalysis, nextOverview] = await Promise.all([
        api.analysis(symbol, strategy),
        api.overview(),
      ])
      setAnalysis(nextAnalysis)
      setOverview(nextOverview)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '刷新失败')
    } finally {
      setRefreshing(false)
    }
  }, [symbol, strategy])

  const currentStrategy = useMemo(
    () => strategies.find((item) => item.id === strategy),
    [strategies, strategy],
  )

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">P</span>
          <span><strong>PLATANIA</strong><small>量化研究</small></span>
        </div>
        <nav aria-label="主导航">
          <a href="#workspace" className="active"><LineChart size={18} />研究工作台</a>
          <a href="#candidates"><Search size={18} />策略选股</a>
          <a href="#backtest"><BarChart3 size={18} />历史回测</a>
        </nav>
        <div className="sidebar-status">
          <Database size={17} />
          <span><strong>本地行情缓存</strong><small>按需手动更新</small></span>
        </div>
        <div className="sidebar-footer">
          <ShieldCheck size={17} />
          <span>研究工具 · 非投资建议</span>
        </div>
      </aside>

      <main id="workspace">
        <header className="topbar">
          <div className="market-status"><span /> A股 · 日线研究</div>
          <div className="topbar-actions">
            <label className="stock-picker">
              <Search size={17} />
              <select value={symbol} onChange={(event) => setSymbol(event.target.value)} aria-label="选择股票">
                {stocks.map((stock) => <option key={stock.symbol} value={stock.symbol}>{stock.symbol} {stock.name}</option>)}
              </select>
            </label>
            <button className="icon-button" onClick={refresh} disabled={refreshing} title="刷新当前标的行情">
              <RefreshCw size={18} className={refreshing ? 'spin' : ''} />
              <span className="sr-only">刷新行情</span>
            </button>
          </div>
        </header>

        {error && <div className="error-banner" role="alert">{error}</div>}

        {analysis ? (
          <>
            <section className="instrument-header">
              <div>
                <div className="instrument-title">
                  <h1>{analysis.stock.name}</h1>
                  <span>{analysis.stock.symbol}.{analysis.stock.exchange}</span>
                  <span>{analysis.stock.sector}</span>
                </div>
                <div className="quote-line">
                  <strong>{analysis.quote.close.toFixed(2)}</strong>
                  <span className={priceClass(analysis.quote.change)}>{formatPercent(analysis.quote.change)}</span>
                  <small>{analysis.quote.date} 收盘</small>
                </div>
              </div>
              <div className="source-status">
                <span className={analysis.data_meta.is_demo ? 'demo-dot' : 'live-dot'} />
                <div>
                  <strong>{analysis.data_meta.is_demo ? '演示行情' : 'AKShare 缓存'}</strong>
                  <small>{new Date(analysis.data_meta.updated_at).toLocaleString('zh-CN')}</small>
                </div>
              </div>
            </section>

            <section className="strategy-bar">
              <div className="segmented-control" aria-label="选择策略">
                {strategies.map((item) => (
                  <button
                    key={item.id}
                    className={item.id === strategy ? 'active' : ''}
                    onClick={() => setStrategy(item.id)}
                  >{item.name}</button>
                ))}
              </div>
              <p>{currentStrategy?.description}</p>
            </section>

            <section className="analysis-layout">
              <div className="chart-section">
                <div className="section-heading compact">
                  <div>
                    <p className="eyebrow">PRICE ACTION</p>
                    <h2>日线与策略信号</h2>
                  </div>
                  <div className="chart-legend"><span className="ma20">MA20</span><span className="ma60">MA60</span><span className="ma120">MA120</span></div>
                </div>
                {loading ? <LoadingBlock /> : <PriceChart bars={analysis.bars} />}
                <div className="signal-strip">
                  <div><span>综合评分</span><strong>{analysis.signal.score}</strong><small>/ 100</small></div>
                  <div><span>状态</span><strong>{analysis.signal.rating}</strong><small>{analysis.signal.position}</small></div>
                  <div><span>60日动量</span><strong className={priceClass(analysis.signal.momentum_60d)}>{formatPercent(analysis.signal.momentum_60d)}</strong><small>价格强度</small></div>
                  <div><span>RSI 14</span><strong>{analysis.signal.rsi14?.toFixed(1) ?? '—'}</strong><small>相对强弱</small></div>
                  <div><span>量比</span><strong>{analysis.signal.volume_ratio?.toFixed(2) ?? '—'}</strong><small>20日均量</small></div>
                </div>
              </div>

              <aside className="candidate-section" id="candidates">
                <div className="section-heading compact">
                  <div>
                    <p className="eyebrow">WATCHLIST</p>
                    <h2>研究池排行</h2>
                  </div>
                  {overview && <span className="breadth">{overview.advancers} 涨 / {overview.decliners} 跌</span>}
                </div>
                {overview ? (
                  <CandidateTable candidates={overview.candidates} selectedSymbol={symbol} onSelect={setSymbol} />
                ) : <LoadingBlock />}
              </aside>
            </section>

            <div id="backtest"><BacktestPanel backtest={analysis.backtest} /></div>
          </>
        ) : <LoadingBlock large />}
      </main>
    </div>
  )
}

function LoadingBlock({ large = false }: { large?: boolean }) {
  return <div className={`loading-block ${large ? 'large' : ''}`}><LoaderCircle size={22} className="spin" /><span>正在计算策略数据</span></div>
}

export default App

