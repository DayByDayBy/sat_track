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
      <ObserverControls
        satellites={satellites}
        selectedSatId={selectedSatId}
        onSelectSatellite={setSelectedSatId}
        onGroundTrackLoaded={setGroundTrack}
        style={{
          width: '100%',
          borderLeft: 'none',
          borderBottom: '1px solid #ddd',
        }}
      />
      <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
        <GlobeView
          satellites={satellites}
          selectedSatId={selectedSatId}
          onSatelliteClick={setSelectedSatId}
          groundTrack={groundTrack ?? undefined}
        />
      </div>
    </div>
  )
}

export default App
