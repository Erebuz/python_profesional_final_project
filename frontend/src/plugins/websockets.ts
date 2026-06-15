import { BASE } from '@/plugins/http-common'
import VueNativeSock from 'vue-native-websocket-vue3'
import { App } from 'vue'
import store from '@/store'

export const ws_url = 'ws://' + new URL(BASE).host + '/websocket'

const ws_options = {
  format: 'json',
  store: store,
  connectManually: false,
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 3000,
}

export function appUseWebSocket(app: App<Element>) {
  app.use(VueNativeSock, ws_url, ws_options)

  app.config.globalProperties.$socket = VueNativeSock
}
