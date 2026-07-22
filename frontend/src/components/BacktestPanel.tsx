import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import type { Backtest } from '../types'
import { formatPercent, priceClass } from '../utils'

export function BacktestPanel({ backtest }: { backtest: Backtest }) {
  const metrics = [
    ['策略收益', formatPercent(backtest.total_return), backtest.total_return],
    ['年化收益', formatPercent(backtest.annualized_return), backtest.annualized_return],
    ['同期基准', formatPercent(backtest.benchmark_return), backtest.benchmark_return],
    ['最大回撤', formatPercent(backtest.max_drawdown), backtest.max_drawdown],
    ['夏普比率', backtest.sharpe.toFixed(2), backtest.sharpe],
    ['胜率', formatPercent(backtest.win_rate), backtest.win_rate],
  ] as const

  return (
    <section className="backtest-section">
      <div className="section-heading">
        <div>
          <p className="eyebrow">BACKTEST</p>
          <h2>策略回测</h2>
        </div>
        <p>{backtest.trade_count} 笔已完成交易 · 初始资金 ¥{backtest.initial_cash.toLocaleString('zh-CN')}</p>
      </div>
      <div className="metrics-grid">
        {metrics.map(([label, value, raw]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong className={label === '最大回撤' ? 'negative' : priceClass(raw)}>{value}</strong>
          </div>
        ))}
      </div>
      <div className="trades-block">
        <h3>最近交易</h3>
        {backtest.trades.length ? (
          <div className="trade-list">
            {backtest.trades.slice(-5).reverse().map((trade) => (
              <div className="trade-row" key={`${trade.entry_date}-${trade.exit_date}`}>
                <span className={`trade-icon ${trade.pnl >= 0 ? 'positive' : 'negative'}`}>
                  {trade.pnl >= 0 ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                </span>
                <span>{trade.entry_date} → {trade.exit_date}</span>
                <span>{trade.quantity.toLocaleString('zh-CN')} 股</span>
                <strong className={priceClass(trade.pnl)}>{formatPercent(trade.return)}</strong>
                <strong className={priceClass(trade.pnl)}>¥{trade.pnl.toLocaleString('zh-CN')}</strong>
              </div>
            ))}
          </div>
        ) : <p className="empty-state">当前回测区间没有已完成交易</p>}
      </div>
      <p className="assumption-note">回测按次日开盘成交，计入佣金、印花税、滑点与 100 股整手约束。历史结果不代表未来表现。</p>
    </section>
  )
}

