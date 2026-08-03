import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'apple-touch-icon.svg'],
      manifest: {
        name: 'مدیریت فروشگاه سی‌تی‌تل',
        short_name: 'سی‌تی‌تل',
        description: 'فروش، انبار، مشتریان و تعمیرات فروشگاه سی‌تی‌تل',
        theme_color: '#0f766e',
        background_color: '#f5f8f7',
        display: 'standalone',
        orientation: 'portrait-primary',
        lang: 'fa',
        dir: 'rtl',
        start_url: '/',
        scope: '/',
        icons: [
          {
            src: '/pwa-icon.svg',
            sizes: 'any',
            type: 'image/svg+xml',
            purpose: 'any maskable',
          },
        ],
      },
      workbox: {
        navigateFallback: '/index.html',
        globPatterns: ['**/*.{js,css,html,svg,woff2}'],
      },
      devOptions: {
        enabled: true,
      },
    }),
  ],
})
