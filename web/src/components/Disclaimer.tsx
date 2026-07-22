import { ShieldAlert } from 'lucide-react'

export function Disclaimer({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`disclaimer ${compact ? 'compact' : ''}`} role="note">
      <ShieldAlert size={16} aria-hidden="true" />
      <span>仅供量化研究与历史回测，不构成投资建议。历史表现不代表未来收益。</span>
    </div>
  )
}

