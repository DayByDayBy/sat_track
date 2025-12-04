import { useState } from 'react'
import GlobeView from './components/GlobeView'
import { useSatelliteStream } from './hooks/useSatelliteStream'
import './App.css'

function App() {
  const { satellites, lastUpdated, connected, error } = useSatelliteStream()
  const [selectedSatId, setSelectedSatId] = useState<string | undefined>()

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
      </div>
      <div style={{ flex: 1, position: 'relative' }}>
        <GlobeView
          satellites={satellites}
          selectedSatId={selectedSatId}
          onSatelliteClick={setSelectedSatId}
        />
      </div>
    </div>
  )
}

export default App
