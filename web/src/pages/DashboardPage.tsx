import { ArrowRight, Bot, ChartNoAxesCombined, Clock3, Database, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Disclaimer } from '../components/Disclaimer'
import { ErrorState, LoadingState } from '../components/PageState'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'

export function DashboardPage() {
  const { data, loading, error, retry } = useAsync(() => Promise.all([api.marketStatus(), api.instruments(), api.strategies()]), [])
  if (loading) return <LoadingState />
  if (error || !data) return <ErrorState error={error ?? new Error('无数据')} retry={retry} />
  const [status, instruments, strategies] = data
  return (
    <div className="page">
      <div className="page-header">
        <div><p className="eyebrow">RESEARCH DESK</p><h1>量化研究仪表盘</h1><p>收盘后信号、历史回测与研究内容集中查看</p></div>
        <div className={`mode-chip ${status.data_kind}`}><Database size={15} />{status.data_kind === 'demo' ? '演示行情模式' : '真实缓存模式'}</div>
      </div>
      <Disclaimer />
      <section className="summary-band">
        <div><span>市场</span><strong>{status.market}</strong><small>{status.session === 'closed' ? '已收盘' : status.session}</small></div>
        <div><span>最新交易日</span><strong>{status.latest_trade_date}</strong><small>{status.data_source}</small></div>
        <div><span>研究池</span><strong>{instruments.items.length} 个标的</strong><small>A股日线</small></div>
        <div><span>策略引擎</span><strong>{strategies.items.length} 套策略</strong><small>下一交易日执行</small></div>
      </section>
      <div className="dashboard-grid">
        <section className="workspace-panel">
          <div className="section-heading"><div><p className="eyebrow">MARKET</p><h2>A股研究池</h2></div><Link to="/market" className="text-link">查看全部<ArrowRight size={14} /></Link></div>
          <div className="instrument-list">
            {instruments.items.slice(0, 6).map((item) => <Link to={`/stocks/${item.symbol}`} key={item.symbol}><span><strong>{item.name}</strong><small>{item.symbol} · {item.sector}</small></span><ChartNoAxesCombined size={17} /></Link>)}
          </div>
        </section>
        <section className="workspace-panel">
          <div className="section-heading"><div><p className="eyebrow">WORKFLOW</p><h2>今日研究流程</h2></div></div>
          <div className="workflow-list">
            <Link to="/market"><TrendingUp size={18} /><span><strong>检查市场与信号</strong><small>读取平台缓存，不触发外部行情请求</small></span></Link>
            <Link to="/ai-workshop"><Bot size={18} /><span><strong>生成 StrategySpec</strong><small>白名单校验后再进入回测</small></span></Link>
            <Link to="/strategies"><Clock3 size={18} /><span><strong>复盘历史策略</strong><small>核对回撤、费用与交易记录</small></span></Link>
          </div>
        </section>
      </div>
      <section className="workspace-panel future-markets">
        <div className="section-heading"><div><p className="eyebrow">ROADMAP</p><h2>市场覆盖</h2></div></div>
        <div className="market-lanes"><span className="active">A股 <small>日线已支持</small></span><span>港股 <small>即将支持</small></span><span>美股 <small>即将支持</small></span><span>加密货币 <small>即将支持</small></span></div>
      </section>
    </div>
  )
}

