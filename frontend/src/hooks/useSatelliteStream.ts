import { useEffect, useRef, useState } from 'react'

export interface SatellitePositions {
  [name: string]: {
    lat: number
    lon: number
    alt_km: number
  }
}

export interface StreamState {
  satellites: SatellitePositions
  lastUpdated: string | null
  connected: boolean
  error: string | null
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/ws/satellites'
const RECONNECT_BASE_DELAY_MS = 1000
const RECONNECT_MAX_DELAY_MS = 15000

export function useSatelliteStream() {
  const [state, setState] = useState<StreamState>({
    satellites: {},
    lastUpdated: null,
    connected: false,
    error: null,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const shouldReconnectRef = useRef(true)
  const attemptRef = useRef(0)

  useEffect(() => {
    shouldReconnectRef.current = true

    const cleanupSocket = () => {
      if (wsRef.current) {
        wsRef.current.onopen = null
        wsRef.current.onmessage = null
        wsRef.current.onclose = null
        wsRef.current.onerror = null
        try {
          wsRef.current.close()
        } catch (_) {
          /* noop */
        }
        wsRef.current = null
      }
    }

    const clearReconnectTimer = () => {
      if (reconnectTimeoutRef.current !== null) {
        window.clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
    }

    const scheduleReconnect = () => {
      if (!shouldReconnectRef.current) {
        return
      }
      attemptRef.current += 1
      const delay = Math.min(
        RECONNECT_BASE_DELAY_MS * 2 ** (attemptRef.current - 1),
        RECONNECT_MAX_DELAY_MS,
      )
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect()
      }, delay)
    }

    const connect = () => {
      if (!shouldReconnectRef.current) {
        return
      }

      clearReconnectTimer()
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        attemptRef.current = 0
        setState(prev => ({ ...prev, connected: true, error: null }))
      }

      ws.onmessage = event => {
        try {
          const data = JSON.parse(event.data)
          setState(prev => ({
            ...prev,
            satellites: data.satellites || {},
            lastUpdated: data.last_updated || null,
            error: null,
          }))
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
          setState(prev => ({ ...prev, error: 'Failed to parse message' }))
        }
      }

      ws.onclose = () => {
        setState(prev => ({ ...prev, connected: false }))
        if (shouldReconnectRef.current) {
          scheduleReconnect()
        }
      }

      ws.onerror = () => {
        setState(prev => ({ ...prev, error: 'WebSocket error', connected: false }))
        // force close to trigger onclose handler
        try {
          ws.close()
        } catch (_) {
          /* noop */
        }
      }
    }

    connect()

    return () => {
      shouldReconnectRef.current = false
      clearReconnectTimer()
      cleanupSocket()
    }
  }, [])

  return state
}
