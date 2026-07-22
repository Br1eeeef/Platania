import { Bell, CheckCheck } from 'lucide-react'

const notifications = [
  { title: '演示信号更新', body: '趋势动量研究池已完成收盘后计算。', time: '18 分钟前' },
  { title: '策略版本更新', body: '均值回归策略新增最大持仓时间约束。', time: '昨天' },
  { title: '数据缓存状态', body: '当前使用确定性演示行情；真实源未在页面请求中调用。', time: '2 天前' },
]

export function NotificationsPage() { return <div className="page narrow"><div className="page-header"><div><p className="eyebrow">NOTIFICATIONS</p><h1>通知中心</h1><p>信号、回测、策略版本与系统状态</p></div><button className="button secondary"><CheckCheck size={15} />全部已读</button></div><div className="notification-list">{notifications.map((item) => <article key={item.title}><Bell size={18} /><div><h2>{item.title}</h2><p>{item.body}</p></div><time>{item.time}</time></article>)}</div></div> }

