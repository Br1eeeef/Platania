import { ArrowLeft, LogIn } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authMode, supabase } from '../services/supabase'

export function AuthPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const submit = async (event: FormEvent) => { event.preventDefault(); if (!supabase) { navigate('/'); return } setLoading(true); setMessage(''); const response = await supabase.auth.signInWithPassword({ email, password }); setLoading(false); if (response.error) setMessage(response.error.message); else navigate('/') }
  return <div className="auth-page"><Link to="/welcome" className="back-link"><ArrowLeft size={16} />返回</Link><div className="auth-brand"><span className="brand-mark">P</span><h1>Platania</h1><p>封闭会员研究空间</p></div><section className="auth-panel"><h2>已有账号登录</h2>{authMode === 'demo' && <div className="data-notice demo">Supabase 尚未配置，当前使用本地 Demo 会员与管理员。</div>}<form onSubmit={(event) => void submit(event)}><label>邮箱<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required disabled={authMode === 'demo'} autoComplete="email" /></label><label>密码<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required disabled={authMode === 'demo'} autoComplete="current-password" /></label>{message && <p className="form-message" role="status">{message}</p>}<button className="button primary full" disabled={loading}><LogIn size={16} />{authMode === 'demo' ? '以 Demo 会员进入' : loading ? '登录中' : '登录'}</button></form><div className="closed-registration"><strong>不开放自助注册</strong><p>先联系 Br1ef 并完成付款，管理员确认后会通过 Supabase 发送邀请邮件。你通过邀请链接自行设置密码，管理员不会看到或保存密码。</p><Link className="button secondary full" to="/membership">申请会员与付款说明</Link></div></section></div>
}
