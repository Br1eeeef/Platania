import {
  Bell, Bot, CandlestickChart, Compass, FlaskConical,
  LayoutDashboard, Settings, ShieldCheck, Star, UserRound, WalletCards,
} from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'
import { Disclaimer } from './Disclaimer'

const navigation = [
  { to: '/', label: '仪表盘', icon: LayoutDashboard },
  { to: '/market', label: 'A股行情', icon: CandlestickChart },
  { to: '/strategies', label: '策略中心', icon: FlaskConical },
  { to: '/ai-workshop', label: 'AI 策略工坊', icon: Bot },
  { to: '/watchlist', label: '自选股', icon: Star },
  { to: '/feed', label: '量化信息流', icon: Compass },
  { to: '/account/membership', label: '会员与用量', icon: WalletCards },
]

const mobileNavigation = navigation.slice(0, 5)

export function AppShell() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/welcome" className="brand" aria-label="Platania 首页">
          <span className="brand-mark">P</span>
          <span><strong>PLATANIA</strong><small>QUANT RESEARCH</small></span>
        </NavLink>
        <nav className="primary-nav" aria-label="主导航">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'}><Icon size={18} /><span>{label}</span></NavLink>
          ))}
        </nav>
        <div className="side-tools">
          <NavLink to="/admin"><ShieldCheck size={17} /><span>管理员</span></NavLink>
          <NavLink to="/notifications"><Bell size={17} /><span>通知</span></NavLink>
          <NavLink to="/settings"><Settings size={17} /><span>设置</span></NavLink>
          <NavLink to="/auth"><UserRound size={17} /><span>账户</span></NavLink>
        </div>
        <Disclaimer compact />
      </aside>
      <main className="main-content">
        <header className="mobile-header">
          <NavLink to="/welcome" className="brand"><span className="brand-mark">P</span><strong>PLATANIA</strong></NavLink>
          <NavLink to="/notifications" className="icon-button" aria-label="通知"><Bell size={18} /></NavLink>
        </header>
        <Outlet />
      </main>
      <nav className="bottom-nav" aria-label="移动端主导航">
        {mobileNavigation.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === '/'}><Icon size={19} /><span>{label.replace('AI 策略工坊', 'AI工坊').replace('策略中心', '策略')}</span></NavLink>
        ))}
      </nav>
    </div>
  )
}
