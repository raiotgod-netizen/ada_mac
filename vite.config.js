import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    base: './', // Important for Electron
    server: {
        port: 5173,
    },
    build: {
        rollupOptions: {
            output: {
                manualChunks: (id) => {
                    if (id.includes('node_modules')) {
                        if (id.includes('@mediapipe') || id.includes('tasks-vision')) {
                            return 'vision_bundle'
                        }
                        if (id.includes('lucide-react')) {
                            return 'icon_lib'
                        }
                        if (id.includes('socket.io')) {
                            return 'socket_lib'
                        }
                        // Separate heavy 3D/CAD deps
                        if (id.includes('three') || id.includes('@react-three')) {
                            return 'cad_vendor'
                        }
                    }
                }
            }
        },
        chunkSizeWarningLimit: 600,
    }
})
