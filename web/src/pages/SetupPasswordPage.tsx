import { ArrowLeft, KeyRound } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { supabase } from '../services/supabase'

export function SetupPasswordPage() {
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [ready, setReady] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('正在验证邀请链接…')

  useEffect(() => {
    if (!supabase) {
      setMessage('Supabase 尚未配置，Demo 模式不发送真实邀请。')
      return
    }
    void supabase.auth.getSession().then(({ data, error }) => {
      setReady(Boolean(data.session) && !error)
      setMessage(error || !data.session ? '邀请链接无效或已过期，请联系 Br1ef 重新邀请。' : '')
    })
  }, [])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (!supabase || password !== confirmation) {
      setMessage('两次输入的密码不一致。')
      return
    }
    setLoading(true)
    setMessage('')
    const { error } = await supabase.auth.updateUser({ password })
    setLoading(false)
    if (error) {
      setMessage(error.message)
      return
    }
    setMessage('密码设置成功，正在进入会员空间。')
    window.setTimeout(() => navigate('/'), 500)
  }

  return <div className="auth-page"><Link to="/welcome" className="back-link"><ArrowLeft size={16} />返回欢迎页</Link><div className="auth-brand"><span className="brand-mark">P</span><h1>设置会员密码</h1><p>密码只提交给 Supabase Auth，管理员无法查看</p></div><section className="auth-panel"><h2>完成邀请</h2><form onSubmit={(event) => void submit(event)}><label>新密码<input type="password" minLength={8} maxLength={128} autoComplete="new-password" required value={password} onChange={(event) => setPassword(event.target.value)} disabled={!ready || loading} /></label><label>确认新密码<input type="password" minLength={8} maxLength={128} autoComplete="new-password" required value={confirmation} onChange={(event) => setConfirmation(event.target.value)} disabled={!ready || loading} /></label>{message && <p className="form-message" role="status">{message}</p>}<button className="button primary full" disabled={!ready || loading || password.length < 8}><KeyRound size={16} />{loading ? '正在保存' : '设置密码并进入'}</button></form><p className="auth-note">不会生成、记录或发送明文临时密码。邀请过期请联系 Br1ef。</p></section></div>
}
