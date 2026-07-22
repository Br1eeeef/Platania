import { ArrowLeft, Check, Clock3, Gauge, Mail } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ErrorState, LoadingState } from '../components/PageState'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'

export function MembershipInfoPage() {
  return <div className="membership-info"><header><Link to="/welcome" className="brand"><span className="brand-mark">P</span><strong>PLATANIA</strong></Link><Link to="/auth" className="button secondary">已有账号登录</Link></header><main><Link to="/welcome" className="text-link"><ArrowLeft size={14} />返回欢迎页</Link><p className="eyebrow">CLOSED MEMBERSHIP</p><h1>封闭付费会员</h1><p className="lead">Platania 不开放自助注册。会员付款由 Br1ef 在线下或其他渠道确认，管理员随后发送账户邀请。</p><div className="membership-steps"><div><span>01</span><h2>联系 Br1ef</h2><p>说明希望使用的套餐与邮箱。不要在聊天或公开页面发送密码、Token 或私钥。</p></div><div><span>02</span><h2>完成付款</h2><p>第一版不接自动支付。管理员仅记录付款备注或外部参考号，不保存支付密码。</p></div><div><span>03</span><h2>接收邀请</h2><p>管理员确认后，Supabase 向你的邮箱发送邀请链接，由你自行设置密码。</p></div><div><span>04</span><h2>激活会员</h2><p>状态为 active 且未到期后，才能访问行情、策略、AI、回测、自选和信息流。</p></div></div><div className="membership-grid"><article><span>研究会员</span><h2>免费 / 体验配置</h2><ul><li><Check size={15} />基础 K 线与指标</li><li><Check size={15} />基础策略和有限回测</li><li><Check size={15} />有限 AI StrategySpec</li></ul></article><article><span>高级研究会员</span><h2>Pro</h2><ul><li><Check size={15} />更高 AI 与回测额度</li><li><Check size={15} />更多自选与高级策略</li><li><Check size={15} />信号提醒与报告导出</li></ul></article></div><section id="contact" className="contact-band"><Mail size={20} /><div><h2>申请会员 / 联系 Br1ef</h2><p>请使用你与 Br1ef 已建立的联系渠道，提供接收邀请的邮箱和希望使用的套餐。不要发送账号密码。</p></div><Link to="/auth" className="button primary">已有账号登录</Link></section><p className="membership-risk">仅供量化研究与历史回测，不构成投资建议。历史表现不代表未来收益。</p></main></div>
}

export function MembershipPage() {
  const { data, loading, error, retry } = useAsync(api.me, [])
  if (loading) return <LoadingState />
  if (error || !data) return <ErrorState error={error ?? new Error('无法加载会员信息')} retry={retry} />
  const usage = data.usage as Record<string, number | string>
  return <div className="page"><div className="page-header"><div><p className="eyebrow">MEMBERSHIP</p><h1>会员与用量</h1><p>状态、到期时间和额度由后端与数据库共同验证</p></div><span className="mode-chip"><Gauge size={15} />{String(usage.plan).toUpperCase()} · {String(usage.status)}</span></div><div className="expiry-band"><Clock3 size={18} /><span>会员到期时间</span><strong>{usage.expires_at ? new Date(String(usage.expires_at)).toLocaleString('zh-CN') : '演示模式'}</strong></div><div className="usage-grid"><Usage label="AI 策略生成" used={Number(usage.ai_used)} limit={Number(usage.ai_limit)} /><Usage label="每日回测" used={Number(usage.backtests_used)} limit={Number(usage.backtests_limit)} /><Usage label="自选股" used={Number(usage.watchlist_used)} limit={Number(usage.watchlist_limit)} /></div><div className="membership-grid"><article><span>当前方案</span><h2>{String(usage.plan).toUpperCase()}</h2><ul><li><Check size={15} />会员状态：{String(usage.status)}</li><li><Check size={15} />后端额度强制校验</li><li><Check size={15} />到期后保留历史记录</li></ul></article><article><span>续费与状态处理</span><h2>联系 Br1ef</h2><p>续费、暂停恢复或状态异常由管理员后台处理。管理员不会要求或查看你的明文密码。</p><Link to="/membership" className="button secondary">查看会员说明</Link></article></div></div>
}

function Usage({ label, used, limit }: { label: string; used: number; limit: number }) { const value = Math.min(100, used / Math.max(limit, 1) * 100); return <div className="usage-item"><div><span>{label}</span><strong>{used} / {limit}</strong></div><div className="usage-track"><span style={{ width: `${value}%` }} /></div></div> }

