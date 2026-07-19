import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import HealthCheckView from '@/views/HealthCheckView.vue'
import DiceView from '@/modules/dice/DiceView.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/health-check', name: 'health-check', component: HealthCheckView },
  { path: '/dice', name: 'dice', component: DiceView },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
