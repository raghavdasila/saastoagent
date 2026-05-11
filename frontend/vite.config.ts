import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const frontendRoot = __dirname
const routeDeckFrameworkRoot = path.resolve(frontendRoot, '../routedeck_framework')
const routeDeckReactEntry = path.resolve(routeDeckFrameworkRoot, 'react/src/index.ts')
const hmrClientPort = process.env.VITE_HMR_CLIENT_PORT
  ? Number(process.env.VITE_HMR_CLIENT_PORT)
  : undefined
const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8085'
const hmrDisabled = process.env.VITE_DISABLE_HMR === 'true'
const apiProxy = {
  '/api': {
    target: apiProxyTarget,
    changeOrigin: true,
  },
}

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: '@', replacement: path.resolve(frontendRoot, './src') },
      { find: '@routedeck/react', replacement: routeDeckReactEntry },
      { find: /^react$/, replacement: path.resolve(frontendRoot, './node_modules/react') },
      { find: 'react/jsx-runtime', replacement: path.resolve(frontendRoot, './node_modules/react/jsx-runtime.js') },
      { find: /^@xyflow\/react$/, replacement: path.resolve(frontendRoot, './node_modules/@xyflow/react/dist/esm/index.js') },
    ],
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    fs: {
      allow: [frontendRoot, routeDeckFrameworkRoot],
    },
    hmr: hmrDisabled
      ? false
      : hmrClientPort
      ? {
          host: 'localhost',
          clientPort: hmrClientPort,
        }
      : undefined,
    proxy: apiProxy,
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
    proxy: apiProxy,
  },
})
