import { useState } from 'react'
import GlobeView from './components/GlobeView'
import ObserverControls from './components/ObserverControls'
import type { GroundTrackPoint, PassEvent } from './components/ObserverControls'
import { useSatelliteStream } from './hooks/useSatelliteStream'
import './App.css'

function App() {
  const { satellites, lastUpdated, connected, error } = useSatelliteStream()
  const [selectedSatId, setSelectedSatId] = useState<string | undefined>()
  const [passes, setPasses] = useState<PassEvent[] | null>(null)
  const [groundTrack, setGroundTrack] = useState<GroundTrackPoint[] | null>(null)

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '1rem', borderBottom: '1px solid #ccc', background: '#fafafa' }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Satellite Tracker</h1>
        <div style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.25rem' }}>
          WebSocket: {connected ? 'connected' : 'disconnected'}
          {lastUpdated && ` | Last updated: ${new Date(lastUpdated).toLocaleTimeString()}`}
          {error && ` | Error: ${error}`}
        </div>
        {selectedSatId && (
          <div style={{ marginTop: '0.5rem' }}>
            Selected: <strong>{selectedSatId}</strong>{' '}
            <button onClick={() => setSelectedSatId(undefined)} style={{ marginLeft: '0.5rem' }}>
              Clear
            </button>
          </div>
        )}
        {passes && (
          <div style={{ marginTop: '0.5rem', fontSize: '0.85rem', color: '#333' }}>
            {passes.length > 0
              ? `Showing ${passes.length} passes`
              : 'No passes in prediction window'}
          </div>
        )}
        {groundTrack && (
          <div style={{ fontSize: '0.85rem', color: '#333' }}>
            {groundTrack.length} ground-track samples loaded
          </div>
        )}
      </div>
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <GlobeView
            satellites={satellites}
            selectedSatId={selectedSatId}
            onSatelliteClick={setSelectedSatId}
          />
        </div>
        <ObserverControls
          satellites={satellites}
          selectedSatId={selectedSatId}
          onSelectSatellite={setSelectedSatId}
          onPassesLoaded={setPasses}
          onGroundTrackLoaded={setGroundTrack}
        />
      </div>
    </div>
  )
}

export default App
