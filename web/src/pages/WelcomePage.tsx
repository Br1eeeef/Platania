import { ArrowRight, Bot, ChartNoAxesCombined, ShieldCheck } from 'lucide-react'
import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { PriceChart } from '../components/PriceChart'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'

export function WelcomePage() {
  const { data } = useAsync(() => Promise.all([api.bars('000300.SH'), api.indicators('000300.SH')]), [])
  const overlays = useMemo(() => new Set(['ma20', 'ma60', 'ma120'] as const), [])
  return <div className="welcome-page"><header className="welcome-nav"><Link to="/welcome" className="brand"><span className="brand-mark">P</span><span><strong>PLATANIA</strong><small>量化研究终端</small></span></Link><nav><Link to="/membership#contact">联系 Br1ef</Link><Link className="button primary" to="/auth">已有账号登录 <ArrowRight size={15} /></Link></nav></header><section className="welcome-hero"><div className="hero-chart" aria-hidden="true">{data && <PriceChart bars={data[0].bars.slice(-260)} indicators={data[1].history.slice(-260)} overlays={overlays} />}</div><div className="hero-overlay" /><div className="hero-content"><p className="eyebrow">QUANT RESEARCH · A-SHARE DAILY</p><h1>Platania</h1><p>量化研究终端、AI 策略工坊与策略信息流社区。</p><div><Link className="button primary" to="/membership">申请会员 <ArrowRight size={16} /></Link><Link className="button ghost" to="/membership#contact">联系 Br1ef</Link><Link className="button ghost" to="/auth">已有账号登录</Link></div><small>平台采用封闭付费会员制。付款确认后由管理员发送 Supabase 邀请，访客不能自助注册。</small></div></section><section className="welcome-capabilities"><article><ChartNoAxesCombined size={22} /><h2>A股日线研究</h2><p>K线、技术指标、策略信号与含交易成本的历史回测。</p></article><article><Bot size={22} /><h2>安全 AI 策略</h2><p>自然语言生成受约束 StrategySpec，不执行任意模型代码。</p></article><article><ShieldCheck size={22} /><h2>研究边界清晰</h2><p>数据来源、演示状态、更新时间和风险提示始终可见。</p></article></section><footer className="welcome-disclaimer">仅供量化研究与历史回测，不构成投资建议。历史表现不代表未来收益。</footer></div>
}
