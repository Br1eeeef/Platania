import { useEffect, useState } from 'react'
import { authMode } from '../services/supabase'

export function SettingsPage() {
  const [redUp, setRedUp] = useState(() => localStorage.getItem('platania-color-mode') !== 'green-up')
  const [dense, setDense] = useState(() => localStorage.getItem('platania-density') === 'dense')
  useEffect(() => { document.documentElement.dataset.colorMode = redUp ? 'red-up' : 'green-up'; localStorage.setItem('platania-color-mode', redUp ? 'red-up' : 'green-up') }, [redUp])
  useEffect(() => { document.documentElement.dataset.density = dense ? 'dense' : 'comfortable'; localStorage.setItem('platania-density', dense ? 'dense' : 'comfortable') }, [dense])
  return <div className="page narrow"><div className="page-header"><div><p className="eyebrow">SETTINGS</p><h1>用户设置</h1><p>显示、数据和账号状态</p></div></div><section className="settings-list"><label><span><strong>中国市场涨跌色</strong><small>上涨使用红色，下跌使用绿色</small></span><input type="checkbox" checked={redUp} onChange={(event) => setRedUp(event.target.checked)} role="switch" /></label><label><span><strong>紧凑信息密度</strong><small>减小表格和面板间距</small></span><input type="checkbox" checked={dense} onChange={(event) => setDense(event.target.checked)} role="switch" /></label><div><span><strong>认证模式</strong><small>配置 Supabase 后自动切换真实会员会话</small></span><span className="state-tag">{authMode}</span></div><div><span><strong>行情调用策略</strong><small>页面只读平台缓存，外部数据源由定时任务更新</small></span><span className="state-tag active">缓存优先</span></div></section></div>
}

