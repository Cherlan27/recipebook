import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: {
        // Absolute URLs point at files in public/, which are served as-is.
        // Turning them into module imports breaks Vitest on Windows
        // ("file:///icons.svg" is not an absolute path there).
        transformAssetUrls: { includeAbsolute: false },
      },
    }),
  ],
  test: {
    environment: 'jsdom',
  },
})
