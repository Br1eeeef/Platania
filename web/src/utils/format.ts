export const percent = (value: number, digits = 2) => `${value >= 0 ? '+' : ''}${(value * 100).toFixed(digits)}%`
export const currency = (value: number) => `¥${value.toLocaleString('zh-CN', { maximumFractionDigits: 2 })}`
export const number = (value: number, digits = 2) => value.toLocaleString('zh-CN', { minimumFractionDigits: digits, maximumFractionDigits: digits })
export const tone = (value: number): 'positive' | 'negative' | 'neutral' => value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral'

