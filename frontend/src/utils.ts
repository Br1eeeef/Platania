export const formatPercent = (value: number) => `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`
export const priceClass = (value: number) => value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral'

