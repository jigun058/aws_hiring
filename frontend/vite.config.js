import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// 개발 중에는 /api를 FastAPI(uvicorn 8000)로 넘긴다. 배포 때는 FastAPI가 dist/를 같은 주소에서 낸다.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
})
