import { Navigate, Outlet } from 'react-router-dom'
import { LoadingState } from './PageState'
import { useAsync } from '../hooks/useAsync'
import { api, ApiError } from '../services/api'

export function ProtectedRoute() {
  const { data, loading, error, retry } = useAsync(api.me, [])
  if (loading) return <LoadingState label="正在验证会员状态" />
  if (error instanceof ApiError && error.status === 401) return <Navigate to="/auth" replace />
  if (error) return <MembershipBlocked message={error.message} retry={retry} />
  if (!data) return <Navigate to="/auth" replace />
  return <Outlet />
}

export function AdminRoute() {
  const { data, loading, error } = useAsync(api.me, [])
  if (loading) return <LoadingState label="正在验证管理员权限" />
  if (error || !data?.user?.is_admin) return <Navigate to="/" replace />
  return <Outlet />
}

function MembershipBlocked({ message, retry }: { message: string; retry: () => void }) {
  return <div className="membership-blocked"><h1>会员访问受限</h1><p>{message}</p><p>账号和历史记录会保留。续费、恢复或状态问题请联系 Br1ef。</p><div><a className="button primary" href="/membership">查看会员说明</a><button className="button secondary" onClick={retry}>重新检查</button></div></div>
}
