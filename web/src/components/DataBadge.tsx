import type { DataMeta } from '../types'

export function DataBadge({ meta }: { meta: DataMeta }) {
  return (
    <div className={`data-badge ${meta.kind}`} title={meta.warnings.join('；')}>
      <span className="status-dot" />
      <div>
        <strong>{meta.kind === 'demo' ? '演示数据' : '真实缓存'}</strong>
        <small>{meta.provider} · {new Date(meta.updated_at).toLocaleString('zh-CN')}</small>
      </div>
    </div>
  )
}

