import { Download, Plus, ShieldCheck } from 'lucide-react'
import { useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ErrorState, LoadingState } from '../components/PageState'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'
import { supabase } from '../services/supabase'

type View = 'dashboard' | 'members' | 'new' | 'usage' | 'audit'

export function AdminPage({ view }: { view: View }) {
  return <div className="page admin-page"><div className="page-header"><div><p className="eyebrow">ADMIN CONSOLE</p><h1>会员管理后台</h1><p>邀请、激活、续费、状态、额度与操作审计</p></div><span className="mode-chip"><ShieldCheck size={15} />管理员</span></div><nav className="admin-nav"><Link className={view === 'dashboard' ? 'active' : ''} to="/admin">概览</Link><Link className={view === 'members' ? 'active' : ''} to="/admin/members">会员</Link><Link className={view === 'new' ? 'active' : ''} to="/admin/members/new">邀请会员</Link><Link className={view === 'usage' ? 'active' : ''} to="/admin/usage">用量</Link><Link className={view === 'audit' ? 'active' : ''} to="/admin/audit-log">审计日志</Link></nav>{view === 'dashboard' && <AdminDashboard />}{view === 'members' && <Members />}{view === 'new' && <InviteMember />}{view === 'usage' && <Usage />}{view === 'audit' && <Audit />}</div>
}

function AdminDashboard() {
  const state = useAsync(api.adminDashboard, [])
  if (state.loading) return <LoadingState />
  if (state.error || !state.data) return <ErrorState error={state.error ?? new Error('无法加载')} retry={state.retry} />
  return <div className="summary-band"><div><span>会员总数</span><strong>{state.data.total}</strong></div><div><span>有效会员</span><strong>{state.data.active}</strong></div><div><span>14日内到期</span><strong>{state.data.expiring_soon}</strong></div><div><span>已暂停</span><strong>{state.data.suspended}</strong></div></div>
}

function Members() {
  const state = useAsync(api.adminMembers, [])
  const update = async (id: string, action: string) => { await api.adminUpdate(id, { action }); await state.retry() }
  const exportCsv = async () => { const session = await supabase?.auth.getSession(); const token = session?.data.session?.access_token; const response = await fetch('/api/admin/members.csv', { headers: token ? { Authorization: `Bearer ${token}` } : {} }); const blob = await response.blob(); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = 'platania-members.csv'; link.click(); URL.revokeObjectURL(link.href) }
  if (state.loading) return <LoadingState />
  if (state.error || !state.data) return <ErrorState error={state.error ?? new Error('无法加载')} retry={state.retry} />
  return <><div className="admin-actions"><Link className="button primary" to="/admin/members/new"><Plus size={15} />邀请会员</Link><button className="button secondary" onClick={() => void exportCsv()}><Download size={15} />导出 CSV</button></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>会员</th><th>套餐</th><th>状态</th><th>到期</th><th>AI / 回测额度</th><th>操作</th></tr></thead><tbody>{state.data.map((member) => <tr key={member.user_id}><td><strong>{member.email || member.user_id}</strong><small>{member.user_id}</small></td><td>{member.plan}</td><td><span className={`state-tag ${member.status === 'active' ? 'active' : ''}`}>{member.status}</span></td><td>{new Date(member.expires_at).toLocaleDateString('zh-CN')}</td><td>{member.ai_quota} / {member.backtest_quota}</td><td><div className="row-actions">{member.status === 'active' ? <button onClick={() => void update(member.user_id, 'suspend')}>暂停</button> : member.status === 'suspended' ? <button onClick={() => void update(member.user_id, 'resume')}>恢复</button> : null}<button className="danger-text" onClick={() => void update(member.user_id, 'ban')}>封禁</button></div></td></tr>)}</tbody></table></div></>
}

function InviteMember() {
  const now = new Date(); const later = new Date(now.getTime() + 30 * 86400000)
  const [form, setForm] = useState({ email: '', plan: 'pro', starts_at: now.toISOString().slice(0,16), expires_at: later.toISOString().slice(0,16), ai_quota: 50, backtest_quota: 200, payment_confirmed: false, payment_note: '', external_payment_reference: '' })
  const [message, setMessage] = useState('')
  const submit = async (event: FormEvent) => { event.preventDefault(); setMessage(''); try { await api.adminInvite({ ...form, starts_at: new Date(form.starts_at).toISOString(), expires_at: new Date(form.expires_at).toISOString() }); setMessage('邀请已发送，会员记录已激活。用户将通过邀请链接自行设置密码。') } catch (reason) { setMessage(reason instanceof Error ? reason.message : '邀请失败') } }
  return <form className="admin-form" onSubmit={(event) => void submit(event)}><div className="data-notice demo">第一版仅支持管理员确认线下付款。不会自动调用支付宝、微信支付，也不会保存用户密码。</div><label>会员邮箱<input type="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label><label>套餐<select value={form.plan} onChange={(event) => setForm({ ...form, plan: event.target.value })}><option value="free">FREE</option><option value="pro">PRO</option></select></label><label>开始时间<input type="datetime-local" required value={form.starts_at} onChange={(event) => setForm({ ...form, starts_at: event.target.value })} /></label><label>到期时间<input type="datetime-local" required value={form.expires_at} onChange={(event) => setForm({ ...form, expires_at: event.target.value })} /></label><label>AI 每日额度<input type="number" min="0" max="10000" value={form.ai_quota} onChange={(event) => setForm({ ...form, ai_quota: Number(event.target.value) })} /></label><label>回测每日额度<input type="number" min="0" max="10000" value={form.backtest_quota} onChange={(event) => setForm({ ...form, backtest_quota: Number(event.target.value) })} /></label><label>付款备注<input value={form.payment_note} onChange={(event) => setForm({ ...form, payment_note: event.target.value })} /></label><label>外部付款参考号<input value={form.external_payment_reference} onChange={(event) => setForm({ ...form, external_payment_reference: event.target.value })} /></label><label className="check-row"><input type="checkbox" checked={form.payment_confirmed} onChange={(event) => setForm({ ...form, payment_confirmed: event.target.checked })} />我已在线下确认收到付款</label>{message && <p className="form-message" role="status">{message}</p>}<button className="button primary" disabled={!form.payment_confirmed}>确认并发送 Supabase 邀请</button></form>
}

function Usage() { const state = useAsync(api.adminUsage, []); if (state.loading) return <LoadingState />; if (state.error || !state.data) return <ErrorState error={state.error ?? new Error('无法加载')} retry={state.retry} />; return <div className="data-table-wrap"><table className="data-table"><thead><tr><th>会员</th><th>AI额度</th><th>回测额度</th></tr></thead><tbody>{state.data.members.map((item) => <tr key={item.user_id}><td>{item.email || item.user_id}</td><td>{item.ai_quota}</td><td>{item.backtest_quota}</td></tr>)}</tbody></table></div> }

function Audit() { const state = useAsync(api.adminAudit, []); const items = useMemo(() => state.data ?? [], [state.data]); if (state.loading) return <LoadingState />; if (state.error) return <ErrorState error={state.error} retry={state.retry} />; return <div className="audit-list">{items.length ? items.map((item) => <article key={item.id}><span className="state-tag">{item.action}</span><strong>{item.target_user_id || '系统'}</strong><time>{new Date(item.created_at).toLocaleString('zh-CN')}</time><code>{JSON.stringify(item.after_state)}</code></article>) : <p>暂无管理员操作记录</p>}</div> }
