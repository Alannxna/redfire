import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react()
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@redfire/ui-components': resolve(__dirname, '../../packages/ui-components/src'),
      '@redfire/business-components': resolve(__dirname, '../../packages/business-components/src'),
      '@redfire/shared-types': resolve(__dirname, '../../packages/shared-types/src'),
      '@redfire/api-client': resolve(__dirname, '../../packages/api-client/src'),
      '@redfire/theme-system': resolve(__dirname, '../../packages/theme-system/src'),
      '@redfire/utils': resolve(__dirname, '../../packages/utils/src'),
    },
  },
  server: {
    port: 3000,
    host: true, // 允许外部访问
    open: false, // 不自动打开浏览器
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true, // 支持websocket
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    target: 'es2020',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          antd: ['antd'],
          utils: ['@tanstack/react-query', 'zustand'],
        },
      },
    },
    // 优化构建性能
    minify: 'esbuild',
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      'antd',
      '@tanstack/react-query'
    ],
  },
  // 开发环境性能优化
  esbuild: {
    logOverride: { 'this-is-undefined-in-esm': 'silent' }
  }
});
