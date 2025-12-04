import { useEffect, useRef } from 'react'
import * as Cesium from 'cesium'

// CESIUM_BASE_URL is defined at build time via Vite's `define`.
declare const CESIUM_BASE_URL: string | undefined

declare global {
  interface Window {
    CESIUM_BASE_URL?: string
  }
}

// Set Cesium base URL at runtime using the global constant if available.
if (typeof window !== 'undefined' && typeof CESIUM_BASE_URL !== 'undefined') {
  window.CESIUM_BASE_URL = CESIUM_BASE_URL
}

export interface SatellitePositions {
  [name: string]: {
    lat: number
    lon: number
    alt_km: number
  }
}

interface GlobeViewProps {
  satellites: SatellitePositions
  selectedSatId?: string
  onSatelliteClick?: (satId: string) => void
}

export default function GlobeView({ satellites, selectedSatId, onSatelliteClick }: GlobeViewProps) {
  const viewerRef = useRef<HTMLDivElement>(null)
  const viewerInstanceRef = useRef<Cesium.Viewer | null>(null)
  const billboardsRef = useRef<Cesium.BillboardCollection | null>(null)
  const imageUnselectedRef = useRef<string | null>(null)
  const imageSelectedRef = useRef<string | null>(null)

  useEffect(() => {
    if (!viewerRef.current) return

    const viewer = new Cesium.Viewer(viewerRef.current, {
      timeline: false,
      animation: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      baseLayerPicker: false,
      navigationHelpButton: false,
      infoBox: false,
      selectionIndicator: false,
    })
    viewerInstanceRef.current = viewer

    // create billboard collection for satellites
    const billboards = viewer.scene.primitives.add(
      new Cesium.BillboardCollection({
        scene: viewer.scene,
      })
    )
    billboardsRef.current = billboards

    // precompute point images (unselected = gold, selected = red)
    const baseCanvas = document.createElement('canvas')
    baseCanvas.width = 16
    baseCanvas.height = 16
    const baseCtx = baseCanvas.getContext('2d')!

    baseCtx.fillStyle = '#FFD700'
    baseCtx.beginPath()
    baseCtx.arc(8, 8, 6, 0, 2 * Math.PI)
    baseCtx.fill()
    imageUnselectedRef.current = baseCanvas.toDataURL()

    baseCtx.clearRect(0, 0, baseCanvas.width, baseCanvas.height)
    baseCtx.fillStyle = '#FF0000'
    baseCtx.beginPath()
    baseCtx.arc(8, 8, 6, 0, 2 * Math.PI)
    baseCtx.fill()
    imageSelectedRef.current = baseCanvas.toDataURL()

    return () => {
      viewer.destroy()
    }
  }, [])

  // update billboards when satellites change
  useEffect(() => {
    const billboards = billboardsRef.current
    if (!billboards) return

    // clear existing billboards
    billboards.removeAll()

    // add billboard for each satellite
    Object.entries(satellites).forEach(([name, pos]) => {
      const cartographic = Cesium.Cartographic.fromDegrees(pos.lon, pos.lat, pos.alt_km * 1000)
      const cartesian = Cesium.Cartesian3.fromRadians(cartographic.longitude, cartographic.latitude, cartographic.height)

      const image =
        selectedSatId === name
          ? imageSelectedRef.current!
          : imageUnselectedRef.current!
      const billboard = billboards.add({
        image,
        position: cartesian,
        width: selectedSatId === name ? 16 : 12,
        height: selectedSatId === name ? 16 : 12,
      })

      // store the satId on the billboard for click handling
      ;(billboard as any).satId = name
    })
  }, [satellites, selectedSatId])

  // Handle clicks on satellites
  useEffect(() => {
    const viewer = viewerInstanceRef.current
    if (!viewer || !onSatelliteClick) return

    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas)
    handler.setInputAction((movement: any) => {
      const pickedObject = viewer.scene.pick(movement.position)
      if (pickedObject && pickedObject.primitive instanceof Cesium.Billboard) {
        const satId = (pickedObject.primitive as any).satId
        if (satId) {
          onSatelliteClick(satId)
        }
      }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK)

    return () => {
      handler.destroy()
    }
  }, [onSatelliteClick])

  return <div ref={viewerRef} style={{ width: '100%', height: '100%' }} />
}
