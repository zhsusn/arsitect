import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function generateRequestId(): string {
  return crypto.randomUUID()
}

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

api.interceptors.request.use(
  (config) => {
    config.headers['X-Request-ID'] = generateRequestId()
    return config
  },
  (error) => Promise.reject(error),
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized globally if needed
      console.warn('Unauthorized request')
    }
    return Promise.reject(error)
  },
)

export { api }
export default api

export type { AxiosRequestConfig }
