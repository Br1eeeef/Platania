import { ArrowRight, SlidersHorizontal } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { ErrorState, LoadingState } from '../components/PageState'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'

export function StrategiesPage() {
  const { data, loading, error, retry } = useAsync(api.strategies, [])
  return <div className="page"><div className="page-header"><div><p className="eyebrow">STRATEGY LIBRARY</p><h1>策略中心</h1><p>可解释、可配置、可回测的 A 股日线策略</p></div></div>{loading ? <LoadingState /> : error ? <ErrorState error={error} retry={retry} /> : <div className="strategy-grid">{data?.items.map((item) => <article className="strategy-card" key={item.id}><SlidersHorizontal size={21} /><div><span className="state-tag">平台策略</span><h2>{item.name}</h2><p>{item.summary}</p><dl>{Object.entries(item.parameters).slice(0,4).map(([key,value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl><Link to={`/strategies/${item.id}`} className="text-link">查看规则与回测<ArrowRight size={14} /></Link></div></article>)}</div>}</div>
}

export function StrategyDetailPage() {
  const { strategyId = '' } = useParams()
  const { data, loading, error, retry } = useAsync(api.strategies, [])
  if (loading) return <LoadingState />
  if (error) return <ErrorState error={error} retry={retry} />
  const strategy = data?.items.find((item) => item.id === strategyId)
  if (!strategy) return <ErrorState error={new Error('策略不存在')} retry={() => history.back()} />
  return <div className="page narrow"><div className="page-header"><div><p className="eyebrow">PLATFORM STRATEGY</p><h1>{strategy.name}</h1><p>{strategy.summary}</p></div></div><section className="document-section"><h2>参数快照</h2><div className="parameter-list">{Object.entries(strategy.parameters).map(([key,value]) => <div key={key}><span>{key}</span><strong>{value}</strong></div>)}</div><h2>执行约束</h2><ul><li>收盘后产生信号，最早在下一交易日开盘执行。</li><li>计入佣金、最低佣金、印花税和滑点。</li><li>停牌时不成交，涨跌停时使用保守的不可成交假设。</li><li>所有历史结果仅用于研究，不代表未来收益。</li></ul><Link to="/market" className="button primary">选择标的运行回测</Link></section></div>
}

