import { useEffect, useRef } from 'react'
import {
  CandlestickSeries,
  ColorType,
  createChart,
  createSeriesMarkers,
  HistogramSeries,
  LineSeries,
  type SeriesMarker,
  type Time,
} from 'lightweight-charts'
import type { Bar } from '../types'

interface PriceChartProps {
  bars: Bar[]
}

export function PriceChart({ bars }: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container || !bars.length) return

    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight,
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#667085',
        fontFamily: 'Inter, "Microsoft YaHei", sans-serif',
      },
      grid: {
        vertLines: { color: '#eef1f4' },
        horzLines: { color: '#eef1f4' },
      },
      rightPriceScale: { borderColor: '#d9dee5', scaleMargins: { top: 0.08, bottom: 0.24 } },
      timeScale: { borderColor: '#d9dee5', timeVisible: false, rightOffset: 4 },
      crosshair: {
        vertLine: { color: '#98a2b3', labelBackgroundColor: '#344054' },
        horzLine: { color: '#98a2b3', labelBackgroundColor: '#344054' },
      },
    })

    const candles = chart.addSeries(CandlestickSeries, {
      upColor: '#c2413a',
      downColor: '#138a63',
      borderUpColor: '#c2413a',
      borderDownColor: '#138a63',
      wickUpColor: '#c2413a',
      wickDownColor: '#138a63',
    })
    candles.setData(
      bars.map((bar) => ({
        time: bar.date as Time,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
      })),
    )

    const addLine = (field: 'ma20' | 'ma60' | 'ma120', color: string, width: 1 | 2) => {
      const series = chart.addSeries(LineSeries, { color, lineWidth: width, priceLineVisible: false, lastValueVisible: false })
      series.setData(
        bars
          .filter((bar) => bar[field] !== null)
          .map((bar) => ({ time: bar.date as Time, value: bar[field] as number })),
      )
    }
    addLine('ma20', '#d38b18', 2)
    addLine('ma60', '#2563a6', 2)
    addLine('ma120', '#7c3f8c', 1)

    const volume = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
      lastValueVisible: false,
      priceLineVisible: false,
    })
    volume.priceScale().applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } })
    volume.setData(
      bars.map((bar) => ({
        time: bar.date as Time,
        value: bar.volume,
        color: bar.close >= bar.open ? '#c2413a55' : '#138a6355',
      })),
    )

    const markers: SeriesMarker<Time>[] = []
    bars.forEach((bar) => {
      if (bar.entry) markers.push({ time: bar.date as Time, position: 'belowBar', color: '#b7791f', shape: 'arrowUp', text: '买' })
      if (bar.exit) markers.push({ time: bar.date as Time, position: 'aboveBar', color: '#344054', shape: 'arrowDown', text: '卖' })
    })
    createSeriesMarkers(candles, markers)
    chart.timeScale().fitContent()

    const observer = new ResizeObserver(() => chart.applyOptions({
      width: container.clientWidth,
      height: container.clientHeight,
    }))
    observer.observe(container)
    return () => {
      observer.disconnect()
      chart.remove()
    }
  }, [bars])

  return <div className="price-chart" ref={containerRef} aria-label="日线 K 线图" />
}
