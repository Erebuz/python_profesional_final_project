import router from '@/router'
import { createAuth } from '@websanova/vue-auth'
import driverHttpAxios from '@websanova/vue-auth/dist/drivers/http/axios.1.x.esm.js'
import driverRouterVueRouter from '@websanova/vue-auth/dist/drivers/router/vue-router.2.x.esm.js'
import authDriver from '@/plugins/authDriver'

import http from '@/plugins/http-common'
import { App } from 'vue'

export interface UserInterface {
  id: string
  username: string
  password?: string
}

const auth = createAuth({
  plugins: {
    http: http,
    router: router,
  },
  drivers: {
    http: driverHttpAxios,
    auth: authDriver,
    router: driverRouterVueRouter,
  },
  options: {
    rolesKey: 'role',
    tokenDefaultKey: 'access_token',
    stores: ['storage'],
    notFoundRedirect: { path: '/' },
    forbiddenRedirect: { path: '/' },
    logoutData: { redirect: '/login', forceRedirect: false },
    loginData: {
      url: '/auth',
      method: 'POST',
      timeout: 5000,
    },
    fetchData: { url: '/auth/me', method: 'GET', enabled: true, timeout: 2000 },
    refreshData: {
      url: '/auth/refresh',
      method: 'POST',
      interval: 20,
      enabled: false,
      timeout: 2000,
    },
    makeRequest: true,
    parseUserData: (req: { me: UserInterface }) => {
      if (req.me === null) {
        auth.logout({}).then(() => {
          localStorage.removeItem('refresh_token')
        })
      }
      return req.me
    },
  },
})

export function appUseAuth(app: App<Element>) {
  app.use(auth)

  app.config.globalProperties.$auth = auth
}

export default auth
