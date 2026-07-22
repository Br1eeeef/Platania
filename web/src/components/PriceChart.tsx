import { useEffect, useRef } from 'react'
import {
  CandlestickSeries, ColorType, createChart, createSeriesMarkers, HistogramSeries, LineSeries,
  type SeriesMarker, type Time,
} from 'lightweight-charts'
import type { Bar, IndicatorPoint } from '../types'

export type Overlay = 'ma5' | 'ma20' | 'ma60' | 'ma120' | 'ema' | 'bollinger'

interface PriceChartProps {
  bars: Bar[]
  indicators: IndicatorPoint[]
  overlays: Set<Overlay>
  signals?: Array<{ date: string; event: string; close: number }>
}

export function PriceChart({ bars, indicators, overlays, signals = [] }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const container = containerRef.current
    if (!container || bars.length === 0) return
    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight,
      layout: { background: { type: ColorType.Solid, color: '#ffffff' }, textColor: '#667085', fontFamily: 'Inter, "Microsoft YaHei", sans-serif' },
      grid: { vertLines: { color: '#edf0f3' }, horzLines: { color: '#edf0f3' } },
      rightPriceScale: { borderColor: '#d9dee5', scaleMargins: { top: 0.06, bottom: 0.24 } },
      timeScale: { borderColor: '#d9dee5', rightOffset: 3, timeVisible: false },
      crosshair: { vertLine: { color: '#98a2b3', labelBackgroundColor: '#344054' }, horzLine: { color: '#98a2b3', labelBackgroundColor: '#344054' } },
      handleScroll: true,
      handleScale: true,
    })
    const candles = chart.addSeries(CandlestickSeries, {
      upColor: '#c2413a', downColor: '#138a63', borderUpColor: '#c2413a', borderDownColor: '#138a63', wickUpColor: '#c2413a', wickDownColor: '#138a63',
    })
    candles.setData(bars.map((bar) => ({ time: bar.date as Time, open: bar.open, high: bar.high, low: bar.low, close: bar.close })))
    const indicatorMap = new Map(indicators.map((point) => [point.date, point]))
    const colors: Record<string, string> = { ma5: '#64748b', ma20: '#d38b18', ma60: '#2563a6', ma120: '#7c3f8c', ema12: '#0e7490', ema26: '#be185d', bollinger_upper: '#98a2b3', bollinger_lower: '#98a2b3' }
    const addLine = (field: keyof IndicatorPoint, color: string, dashed = false) => {
      const series = chart.addSeries(LineSeries, { color, lineWidth: 1, lineStyle: dashed ? 2 : 0, priceLineVisible: false, lastValueVisible: false })
      series.setData(bars.flatMap((bar) => {
        const value = indicatorMap.get(bar.date)?.[field]
        return typeof value === 'number' ? [{ time: bar.date as Time, value }] : []
      }))
    }
    for (const key of ['ma5', 'ma20', 'ma60', 'ma120'] as const) if (overlays.has(key)) addLine(key, colors[key])
    if (overlays.has('ema')) { addLine('ema12', colors.ema12); addLine('ema26', colors.ema26) }
    if (overlays.has('bollinger')) { addLine('bollinger_upper', colors.bollinger_upper, true); addLine('bollinger_lower', colors.bollinger_lower, true) }
    const volume = chart.addSeries(HistogramSeries, { priceFormat: { type: 'volume' }, priceScaleId: 'volume', priceLineVisible: false, lastValueVisible: false })
    volume.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })
    volume.setData(bars.map((bar) => ({ time: bar.date as Time, value: bar.volume, color: bar.close >= bar.open ? '#c2413a4d' : '#138a634d' })))
    const visibleDates = new Set(bars.map((bar) => bar.date))
    const markers: SeriesMarker<Time>[] = signals.filter((signal) => visibleDates.has(signal.date)).slice(-8).map((signal) => ({
      time: signal.date as Time,
      position: signal.event === 'entry' ? 'belowBar' : 'aboveBar',
      color: signal.event === 'entry' ? '#b7791f' : '#344054',
      shape: signal.event === 'entry' ? 'arrowUp' : 'arrowDown',
      text: signal.event === 'entry' ? '买' : '出',
    }))
    createSeriesMarkers(candles, markers)
    chart.timeScale().fitContent()
    const observer = new ResizeObserver(() => chart.applyOptions({ width: container.clientWidth, height: container.clientHeight }))
    observer.observe(container)
    return () => { observer.disconnect(); chart.remove() }
  }, [bars, indicators, overlays, signals])
  return <div ref={containerRef} className="price-chart" aria-label="可缩放股票 K 线、成交量和技术指标图" />
}
