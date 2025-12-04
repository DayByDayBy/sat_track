import { useState } from 'react'
import GlobeView from './components/GlobeView'
import ObserverControls from './components/ObserverControls'
import type { GroundTrackPoint } from './components/ObserverControls'
import { useSatelliteStream } from './hooks/useSatelliteStream'
import './App.css'

function App() {
  const { satellites } = useSatelliteStream()
  const [selectedSatId, setSelectedSatId] = useState<string | undefined>()
  const [groundTrack, setGroundTrack] = useState<GroundTrackPoint[] | null>(null)

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid #ccc', background: '#fafafa' }}>
        <h1 style={{ margin: 0, fontSize: '1.75rem' }}>Satellite Tracker</h1>
      </div>
      <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
        <GlobeView
          satellites={satellites}
          selectedSatId={selectedSatId}
          onSatelliteClick={setSelectedSatId}
          groundTrack={groundTrack ?? undefined}
        />
        <ObserverControls
          satellites={satellites}
          selectedSatId={selectedSatId}
          onSelectSatellite={setSelectedSatId}
          onGroundTrackLoaded={setGroundTrack}
          style={{
            position: 'absolute',
            top: '1rem',
            left: '1rem',
            width: '320px',
            maxHeight: '90%',
            overflowY: 'auto',
            borderRadius: '8px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
            borderLeft: 'none',
          }}
        />
      </div>
    </div>
  )
}

export default App
