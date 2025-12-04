import { useEffect, useMemo, useState } from 'react'

import type { SatellitePositions } from './GlobeView'
import PassPlot from './PassPlot'

export interface PassEvent {
  start: string
  peak: string
  end: string
  max_elevation_deg: number
}

export interface GroundTrackPoint {
  time: string
  lat: number
  lon: number
  alt_km: number
}

interface PassesResponse {
  sat_id: string
  observer: { lat: number; lon: number }
  passes: PassEvent[]
}

interface GroundTrackResponse {
  sat_id: string
  points: GroundTrackPoint[]
}

interface ObserverControlsProps {
  satellites: SatellitePositions
  selectedSatId?: string
  onSelectSatellite: (satId: string) => void
  onPassesLoaded?: (passes: PassEvent[]) => void
  onGroundTrackLoaded?: (points: GroundTrackPoint[]) => void
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export default function ObserverControls({
  satellites,
  selectedSatId,
  onSelectSatellite,
  onPassesLoaded,
  onGroundTrackLoaded,
}: ObserverControlsProps) {
  const [observerLat, setObserverLat] = useState(0)
  const [observerLon, setObserverLon] = useState(0)
  const [passes, setPasses] = useState<PassEvent[] | null>(null)
  const [groundTrack, setGroundTrack] = useState<GroundTrackPoint[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hours, setHours] = useState(12)
  const [minElevation, setMinElevation] = useState(10)

  const satOptions = useMemo(() => Object.keys(satellites).sort(), [satellites])

  useEffect(() => {
    if (!selectedSatId && satOptions.length > 0) {
      onSelectSatellite(satOptions[0])
    }
  }, [selectedSatId, satOptions, onSelectSatellite])

  const fetchPasses = async () => {
    if (!selectedSatId) {
      setError('Select a satellite first')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const url = new URL(`${API_BASE}/api/passes`)
      url.searchParams.set('lat', observerLat.toString())
      url.searchParams.set('lon', observerLon.toString())
      url.searchParams.set('sat_id', selectedSatId)
      url.searchParams.set('hours', hours.toString())
      url.searchParams.set('min_elevation_deg', minElevation.toString())
      const res = await fetch(url)
      if (!res.ok) {
        throw new Error(`Passes request failed: ${res.status}`)
      }
      const data: PassesResponse = await res.json()
      setPasses(data.passes)
      onPassesLoaded?.(data.passes)
    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : 'Failed to fetch passes')
    } finally {
      setLoading(false)
    }
  }

  const fetchGroundTrack = async () => {
    if (!selectedSatId) {
      setError('Select a satellite first')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const url = new URL(`${API_BASE}/api/groundtrack`)
      url.searchParams.set('sat_id', selectedSatId)
      url.searchParams.set('hours', hours.toString())
      const res = await fetch(url)
      if (!res.ok) {
        throw new Error(`Groundtrack request failed: ${res.status}`)
      }
      const data: GroundTrackResponse = await res.json()
      setGroundTrack(data.points)
      onGroundTrackLoaded?.(data.points)
    } catch (err) {
      console.error(err)
      setError(err instanceof Error ? err.message : 'Failed to fetch groundtrack')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ width: '360px', padding: '1rem', borderLeft: '1px solid #ddd', background: '#fff' }}>
      <h2>Observer Controls</h2>
      <label style={{ display: 'block', marginBottom: '0.5rem' }}>
        Satellite
        <select
          value={selectedSatId || ''}
          onChange={e => onSelectSatellite(e.target.value)}
          style={{ width: '100%', marginTop: '0.25rem' }}
        >
          {satOptions.map(name => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </label>
      <label style={{ display: 'block', marginBottom: '0.5rem' }}>
        Observer Latitude
        <input
          type="number"
          value={observerLat}
          onChange={e => setObserverLat(Number(e.target.value))}
          style={{ width: '100%', marginTop: '0.25rem' }}
        />
      </label>
      <label style={{ display: 'block', marginBottom: '0.5rem' }}>
        Observer Longitude
        <input
          type="number"
          value={observerLon}
          onChange={e => setObserverLon(Number(e.target.value))}
          style={{ width: '100%', marginTop: '0.25rem' }}
        />
      </label>
      <label style={{ display: 'block', marginBottom: '0.5rem' }}>
        Prediction Window (hours)
        <input
          type="number"
          min={1}
          max={24}
          value={hours}
          onChange={e => setHours(Number(e.target.value))}
          style={{ width: '100%', marginTop: '0.25rem' }}
        />
      </label>
      <label style={{ display: 'block', marginBottom: '0.5rem' }}>
        Min Elevation (deg)
        <input
          type="number"
          min={0}
          max={90}
          value={minElevation}
          onChange={e => setMinElevation(Number(e.target.value))}
          style={{ width: '100%', marginTop: '0.25rem' }}
        />
      </label>
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
        <button onClick={fetchPasses} disabled={loading}>
          Fetch Passes
        </button>
        <button onClick={fetchGroundTrack} disabled={loading}>
          Ground Track
        </button>
      </div>
      {error && (
        <div style={{ color: 'red', marginTop: '0.5rem' }}>{error}</div>
      )}
      {passes && (
        <div style={{ marginTop: '1rem' }}>
          <h3>Upcoming Passes</h3>
          {passes.length === 0 ? (
            <p>No passes in window.</p>
          ) : (
            <>
              <PassPlot passes={passes} />
              <ul>
                {passes.map((p, idx) => (
                  <li key={idx}>
                    Rise: {new Date(p.start).toLocaleString()} | Peak: {new Date(p.peak).toLocaleString()} |
                    Set: {new Date(p.end).toLocaleString()} | Max elev: {p.max_elevation_deg.toFixed(1)}°
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
      {groundTrack && (
        <div style={{ marginTop: '1rem' }}>
          <h3>Ground Track Points</h3>
          <p>{groundTrack.length} samples</p>
        </div>
      )}
    </div>
  )
}
