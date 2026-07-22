import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { AdminRoute, ProtectedRoute } from './components/ProtectedRoute'
import { AdminPage } from './pages/AdminPage'
import { AiWorkshopPage } from './pages/AiWorkshopPage'
import { AuthPage } from './pages/AuthPage'
import { SetupPasswordPage } from './pages/SetupPasswordPage'
import { BacktestPage } from './pages/BacktestPage'
import { DashboardPage } from './pages/DashboardPage'
import { FeedPage } from './pages/FeedPage'
import { MarketPage } from './pages/MarketPage'
import { MembershipInfoPage, MembershipPage } from './pages/MembershipPage'
import { NotificationsPage } from './pages/NotificationsPage'
import { SettingsPage } from './pages/SettingsPage'
import { StockPage } from './pages/StockPage'
import { StrategiesPage, StrategyDetailPage } from './pages/StrategiesPage'
import { WatchlistPage } from './pages/WatchlistPage'
import { WelcomePage } from './pages/WelcomePage'

export default function App() {
  return (
    <Routes>
      <Route path="/welcome" element={<WelcomePage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/auth/setup-password" element={<SetupPasswordPage />} />
      <Route path="/membership" element={<MembershipInfoPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="market" element={<MarketPage />} />
          <Route path="stocks/:symbol" element={<StockPage />} />
          <Route path="strategies" element={<StrategiesPage />} />
          <Route path="strategies/:strategyId" element={<StrategyDetailPage />} />
          <Route path="ai-workshop" element={<AiWorkshopPage />} />
          <Route path="backtests/:id" element={<BacktestPage />} />
          <Route path="watchlist" element={<WatchlistPage />} />
          <Route path="feed" element={<FeedPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="account/membership" element={<MembershipPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route element={<AdminRoute />}>
            <Route path="admin" element={<AdminPage view="dashboard" />} />
            <Route path="admin/members" element={<AdminPage view="members" />} />
            <Route path="admin/members/new" element={<AdminPage view="new" />} />
            <Route path="admin/usage" element={<AdminPage view="usage" />} />
            <Route path="admin/audit-log" element={<AdminPage view="audit" />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
