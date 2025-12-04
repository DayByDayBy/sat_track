import Plot from 'react-plotly.js'

import type { PassEvent } from './ObserverControls'

interface PassPlotProps {
  passes: PassEvent[]
}

export default function PassPlot({ passes }: PassPlotProps) {
  if (!passes.length) return null

  const x: (string | null)[] = []
  const y: (number | null)[] = []
  const text: (string | null)[] = []

  passes.forEach((p, idx) => {
    x.push(p.start, p.peak, p.end, null)
    y.push(0, p.max_elevation_deg, 0, null)
    const label = `Pass ${idx + 1}`
    text.push(label, label, label, null)
  })

  const data: any[] = [
    {
      x,
      y,
      text,
      mode: 'lines+markers',
      line: { shape: 'linear', color: '#1f77b4' },
      marker: { size: 4 },
    },
  ]

  const layout: any = {
    margin: { l: 40, r: 10, t: 30, b: 40 },
    xaxis: { title: 'Time', type: 'date' },
    yaxis: { title: 'Elevation (deg)', range: [0, 90] },
    height: 240,
  }

  return <Plot data={data} layout={layout} style={{ width: '100%', height: '240px' }} config={{ displayModeBar: false }} />
}
