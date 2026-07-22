import { Download } from 'lucide-react'
import { useLocation, useParams } from 'react-router-dom'
import { Disclaimer } from '../components/Disclaimer'
import { EquityChart } from '../components/EquityChart'
import { ErrorState, LoadingState } from '../components/PageState'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'
import type { BacktestResult } from '../types'
import { currency, percent, tone } from '../utils/format'

export function BacktestPage() {
  const { id = '' } = useParams()
  const location = useLocation()
  const supplied = location.state as BacktestResult | null
  const { data, loading, error, retry } = useAsync(() => supplied ? Promise.resolve(supplied) : api.getBacktest(id), [id])
  if (loading) return <LoadingState label="正在整理回测报告" />
  if (error || !data) return <ErrorState error={error ?? new Error('报告不存在')} retry={retry} />
  const m = data.metrics
  const download = () => { const rows = ['entry_date,exit_date,entry_price,exit_price,quantity,pnl,return_rate,costs', ...data.trades.map((t) => `${t.entry_date},${t.exit_date},${t.entry_price},${t.exit_price},${t.quantity},${t.pnl},${t.return_rate},${t.costs}`)]; const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8' }); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `platania-${data.symbol}-${data.id}.csv`; link.click(); URL.revokeObjectURL(link.href) }
  return <div className="page"><div className="page-header"><div><p className="eyebrow">BACKTEST REPORT</p><h1>回测报告</h1><p>{data.symbol} · {data.strategy_id} · {data.data_range.start} 至 {data.data_range.end}</p></div><button className="button secondary" onClick={download}><Download size={15} />导出 CSV</button></div><Disclaimer /><div className={`data-notice ${data.is_demo ? 'demo' : 'live'}`}>{data.is_demo ? '演示数据回测，不代表真实市场结果' : `数据来源：${data.data_source}`}</div><div className="metric-grid report"><div><span>总收益</span><strong className={tone(m.total_return)}>{percent(m.total_return)}</strong></div><div><span>年化收益</span><strong className={tone(m.annualized_return)}>{percent(m.annualized_return)}</strong></div><div><span>基准收益</span><strong className={tone(m.benchmark_return)}>{percent(m.benchmark_return)}</strong></div><div><span>最大回撤</span><strong className="negative">{percent(m.max_drawdown)}</strong></div><div><span>夏普比率</span><strong>{m.sharpe_ratio.toFixed(2)}</strong></div><div><span>胜率</span><strong>{percent(m.win_rate)}</strong></div><div><span>盈亏比</span><strong>{m.profit_factor?.toFixed(2) ?? '—'}</strong></div><div><span>交易次数</span><strong>{m.trade_count}</strong></div></div><section className="workspace-panel"><div className="section-heading"><h2>权益曲线</h2><span>初始资金 {currency(Number(data.parameters.initial_cash))}</span></div><EquityChart values={data.equity_curve} /></section><section className="workspace-panel"><div className="section-heading"><h2>完整交易记录</h2><span>平均持仓 {m.average_holding_days} 个交易日</span></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>入场</th><th>退出</th><th>数量</th><th>持仓</th><th>收益率</th><th>盈亏</th><th>费用</th></tr></thead><tbody>{data.trades.length ? data.trades.map((trade) => <tr key={`${trade.entry_date}-${trade.exit_date}`}><td>{trade.entry_date}<small>{trade.entry_price}</small></td><td>{trade.exit_date}<small>{trade.exit_price}</small></td><td>{trade.quantity.toLocaleString('zh-CN')}</td><td>{trade.holding_days} 日</td><td className={tone(trade.return_rate)}>{percent(trade.return_rate)}</td><td className={tone(trade.pnl)}>{currency(trade.pnl)}</td><td>{currency(trade.costs)}</td></tr>) : <tr><td colSpan={7}>当前参数与数据范围没有已完成交易</td></tr>}</tbody></table></div></section></div>
}

