import { AlertCircle, Inbox, LoaderCircle, RefreshCw, WifiOff } from 'lucide-react'

export function LoadingState({ label = '正在加载研究数据' }: { label?: string }) {
  return <div className="page-state"><LoaderCircle className="spin" size={22} /><span>{label}</span></div>
}

export function ErrorState({ error, retry }: { error: Error; retry: () => void }) {
  const offline = !navigator.onLine
  const Icon = offline ? WifiOff : AlertCircle
  return (
    <div className="page-state error" role="alert">
      <Icon size={24} />
      <strong>{offline ? '当前处于离线状态' : '数据加载失败'}</strong>
      <span>{error.message}</span>
      <button className="button secondary" onClick={retry}><RefreshCw size={15} />重试</button>
    </div>
  )
}

export function EmptyState({ label = '暂无数据' }: { label?: string }) {
  return <div className="page-state"><Inbox size={24} /><span>{label}</span></div>
}

