import { createApp } from 'vue'
import App from './App.vue'
import { appUseRouter } from './router'
import { appUseHttp } from '@/plugins/http-common'
import { appUseAuth } from '@/plugins/auth'
import store from './store'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { appUseWebSocket } from '@/plugins/websockets'

const app = createApp(App)
appUseRouter(app)
appUseHttp(app)
appUseAuth(app)
app.use(store)
appUseWebSocket(app)

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
})

app.use(vuetify)

app.mount('#app')
