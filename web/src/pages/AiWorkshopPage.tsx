import { Bot, Braces, Play, Search, Send, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Disclaimer } from '../components/Disclaimer'
import { api } from '../services/api'
import type { Instrument, StrategySpec } from '../types'

const example = '帮我生成一个A股趋势策略，排除ST，MA20上穿MA60买入，跌破MA20或者亏损8%退出，单只股票最大仓位10%。'
const symbolPattern = /^\d{6}\.(SH|SZ)$/

type AiResult = {
  mode: string
  spec: StrategySpec
  readable_code: string
  daily_used: number
  daily_limit: number
  disclaimer: string
}

export function AiWorkshopPage() {
  const navigate = useNavigate()
  const [prompt, setPrompt] = useState(example)
  const [result, setResult] = useState<AiResult | null>(null)
  const [symbol, setSymbol] = useState('600519.SH')
  const [selectedName, setSelectedName] = useState('')
  const [instrumentOptions, setInstrumentOptions] = useState<Instrument[]>([])
  const [instrumentLoading, setInstrumentLoading] = useState(false)
  const [instrumentError, setInstrumentError] = useState('')
  const [initialCash, setInitialCash] = useState(100_000)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const query = symbol.trim()
    if (query.length < 2) {
      setInstrumentOptions([])
      setInstrumentLoading(false)
      return
    }
    let cancelled = false
    setInstrumentLoading(true)
    setInstrumentError('')
    const timer = window.setTimeout(() => {
      void api.instruments(1, query).then((response) => {
        if (cancelled) return
        setInstrumentOptions(response.items)
        const exact = response.items.find((item) => item.symbol === query.toUpperCase())
        if (exact) setSelectedName(exact.name)
      }).catch(() => {
        if (!cancelled) setInstrumentError('暂时无法搜索股票目录，可直接输入标准股票代码')
      }).finally(() => {
        if (!cancelled) setInstrumentLoading(false)
      })
    }, 250)
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [symbol])

  const generate = async () => {
    setLoading(true)
    setError('')
    try {
      setResult(await api.aiGenerate(prompt))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '生成失败')
    } finally {
      setLoading(false)
    }
  }

  const updateRisk = (field: 'stop_loss_pct' | 'max_position', value: number) => {
    setResult((current) => current
      ? { ...current, spec: { ...current.spec, risk: { ...current.spec.risk, [field]: value } } }
      : current)
  }

  const backtest = async () => {
    if (!result) return
    const normalizedSymbol = symbol.trim().toUpperCase()
    if (!symbolPattern.test(normalizedSymbol)) {
      setError('请从搜索建议中选择股票，或输入 600519.SH 这样的标准代码')
      return
    }
    if (initialCash < 10_000 || initialCash > 100_000_000) {
      setError('初始资金必须在 1 万元至 1 亿元之间')
      return
    }
    setLoading(true)
    setError('')
    try {
      const report = await api.aiBacktest(normalizedSymbol, result.spec, initialCash)
      navigate(`/backtests/${report.id}`, { state: report })
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '回测失败')
    } finally {
      setLoading(false)
    }
  }

  const validBacktestConfig = symbolPattern.test(symbol.trim().toUpperCase())
    && initialCash >= 10_000
    && initialCash <= 100_000_000

  return <div className="page"><div className="page-header"><div><p className="eyebrow">AI STRATEGY LAB</p><h1>AI 策略工坊</h1><p>自然语言 → StrategySpec → 白名单校验 → 平台回测</p></div><span className={`mode-chip ${result?.mode === 'deepseek' ? 'live' : 'demo'}`}><Bot size={15} />{result?.mode === 'deepseek' ? 'DeepSeek' : 'Mock 可用'}</span></div><Disclaimer />
    <div className="ai-layout"><section className="prompt-panel"><label htmlFor="strategy-prompt">描述策略规则</label><textarea id="strategy-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} maxLength={2000} /><div className="prompt-footer"><span>{prompt.length} / 2000</span><button className="button primary" disabled={loading || prompt.trim().length < 10} onClick={() => void generate()}><Send size={15} />{loading ? '正在生成' : '生成受约束策略'}</button></div>{error && <p className="form-error" role="alert">{error}</p>}<div className="security-list"><h3><ShieldCheck size={17} />安全边界</h3><span>只接受 JSON StrategySpec</span><span>指标与操作符白名单</span><span>不执行模型返回的 Python</span><span>无文件、Shell、环境变量与网络权限</span></div></section>
      <section className="spec-panel">{result ? <><div className="section-heading"><div><p className="eyebrow">VALIDATED SPEC</p><h2>{result.spec.name}</h2></div><span className="state-tag active">已校验</span></div><div className="spec-summary"><div><span>市场</span><strong>{result.spec.market}</strong></div><div><span>调仓</span><strong>{result.spec.rebalance_frequency}</strong></div><div><span>基准</span><strong>{result.spec.benchmark}</strong></div></div><div className="parameter-editor"><label>止损比例<input type="number" min="1" max="20" step="1" value={result.spec.risk.stop_loss_pct * 100} onChange={(event) => updateRisk('stop_loss_pct', Number(event.target.value) / 100)} /><span>%</span></label><label>最大仓位<input type="number" min="1" max="50" step="1" value={result.spec.risk.max_position * 100} onChange={(event) => updateRisk('max_position', Number(event.target.value) / 100)} /><span>%</span></label></div><div className="condition-block"><h3>入场条件</h3>{result.spec.entry_conditions.map((condition, index) => <code key={index}>{JSON.stringify(condition)}</code>)}<h3>退出条件</h3>{result.spec.exit_conditions.map((condition, index) => <code key={index}>{JSON.stringify(condition)}</code>)}</div><details><summary><Braces size={15} />查看只读策略代码</summary><pre>{result.readable_code}</pre></details>
        <section className="ai-backtest-config" aria-labelledby="ai-backtest-title"><div className="ai-backtest-heading"><div><p className="eyebrow">BACKTEST CONFIG</p><h3 id="ai-backtest-title">选择回测股票与资金</h3></div><ShieldCheck size={17} aria-label="参数将在后端校验" /></div><div className="ai-backtest-grid"><label htmlFor="ai-backtest-symbol">回测股票<span className="stock-search-input"><Search size={15} aria-hidden="true" /><input id="ai-backtest-symbol" list="ai-stock-options" value={symbol} onChange={(event) => { setSymbol(event.target.value); setSelectedName('') }} placeholder="输入股票代码或名称搜索" autoComplete="off" aria-describedby="ai-stock-hint" /></span><datalist id="ai-stock-options">{instrumentOptions.map((item) => <option key={item.symbol} value={item.symbol}>{item.name} · {item.sector}</option>)}</datalist><small id="ai-stock-hint">{instrumentLoading ? '正在搜索全市场目录…' : instrumentError || (selectedName ? `已选择：${selectedName}（${symbol.toUpperCase()}）` : '支持按代码、名称或行业搜索，选择后显示标准代码')}</small></label><label htmlFor="ai-initial-cash">初始资金（元）<input id="ai-initial-cash" type="number" min="10000" max="100000000" step="10000" value={initialCash} onChange={(event) => setInitialCash(Number(event.target.value))} required /><small>允许范围：1 万元至 1 亿元</small></label></div></section>
        <div className="spec-actions"><small>今日 {result.daily_used} / {result.daily_limit} 次 · 回测参数将写入报告</small><button className="button primary" disabled={loading || !validBacktestConfig} onClick={() => void backtest()}><Play size={15} />{loading ? '正在运行回测' : `对 ${selectedName || symbol.toUpperCase()} 运行回测`}</button></div></> : <div className="empty-spec"><Bot size={32} /><strong>等待生成 StrategySpec</strong><span>未配置 DeepSeek Key 时会返回明确标记的确定性 Mock 结果。</span></div>}</section></div>
  </div>
}
