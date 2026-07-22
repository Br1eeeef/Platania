import { useId } from 'react'

export function EquityChart({ values, label = '收益曲线' }: { values: Array<{ date: string; value: number }>; label?: string }) {
  const id = useId().replace(/:/g, '')
  if (values.length < 2) return null
  const width = 900
  const height = 220
  const numbers = values.map((item) => item.value)
  const min = Math.min(...numbers)
  const max = Math.max(...numbers)
  const range = max - min || 1
  const points = values.map((item, index) => `${(index / (values.length - 1)) * width},${height - ((item.value - min) / range) * (height - 20) - 10}`).join(' ')
  return (
    <svg className="equity-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label} preserveAspectRatio="none">
      <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#2563a6" stopOpacity=".22" /><stop offset="1" stopColor="#2563a6" stopOpacity="0" /></linearGradient></defs>
      <polygon points={`0,${height} ${points} ${width},${height}`} fill={`url(#${id})`} />
      <polyline points={points} fill="none" stroke="#2563a6" strokeWidth="2" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

