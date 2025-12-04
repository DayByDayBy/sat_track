import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    CESIUM_BASE_URL: JSON.stringify('https://cesium.com/downloads/cesiumjs/releases/1.123/Build/Cesium/'),
  },
})
