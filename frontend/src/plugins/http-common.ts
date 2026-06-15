import axios, { AxiosHeaders, AxiosStatic } from 'axios'
import { App } from 'vue'
import VueAxios from 'vue-axios'

const debug_ip = 'localhost'
const port = ':8080'
const stream_port = ':8888'

export const BASE =
  process.env.NODE_ENV !== 'production'
    ? 'http://' + debug_ip + port
    : 'http://' + window.location.host

export const STREAM_BASE =
  process.env.NODE_ENV !== 'production'
    ? 'http://' + debug_ip + stream_port
    : 'http://' + window.location.hostname + stream_port

const instance = axios.create({
  baseURL: BASE,
  headers: {
    'Content-type': 'application/json',
  },
})

instance.interceptors.request.use(function (config) {
  const token = localStorage.getItem('access_token')

  if (config.headers === undefined) {
    config.headers = {} as AxiosHeaders
  }

  config.headers.Authorization = token ? `Bearer ${token}` : ''
  if (config.url === '/auth/refresh') {
    if (localStorage.getItem('refresh_token')) {
      const refresh_token = localStorage.getItem('refresh_token')
      config.data = { refresh_token: refresh_token }
    }
  }
  return config
})

instance.interceptors.response.use(function (config) {
  if (config.data?.refresh_token) {
    const refreshToken = config.data.refresh_token
    localStorage.setItem('refresh_token', refreshToken)
  }
  return config
})

export function appUseHttp(app: App<Element>) {
  app.use(VueAxios, instance as AxiosStatic)
}

export default instance
