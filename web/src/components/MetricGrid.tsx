export function MetricGrid({ items }: { items: Array<{ label: string; value: string; tone?: 'positive' | 'negative' | 'neutral'; note?: string }> }) {
  return <div className="metric-grid">{items.map((item) => <div className="metric" key={item.label}><span>{item.label}</span><strong className={item.tone}>{item.value}</strong>{item.note && <small>{item.note}</small>}</div>)}</div>
}

