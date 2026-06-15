import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import HomeView from '../views/LoginView.vue'
import GeneralView from '@/views/GeneralView.vue'
import { App } from 'vue'
import UserView from '@/views/UserView.vue'
import ChartView from '@/views/ChartView.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'login',
    component: HomeView,
    meta: {
      auth: false,
    },
  },
  {
    path: '/',
    name: 'general',
    component: GeneralView,
    meta: {
      auth: true,
      layout: 'default',
    },
  },
  {
    path: '/user',
    name: 'user',
    component: UserView,
    meta: {
      auth: true,
      layout: 'default',
    },
  },
  {
    path: '/chart',
    name: 'chart',
    component: ChartView,
    meta: {
      auth: true,
      layout: 'default',
    },
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
})

export function appUseRouter(app: App<Element>) {
  app.use(router)
}
export default router
