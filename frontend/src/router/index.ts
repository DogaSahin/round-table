import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import HealthCheckView from '@/views/HealthCheckView.vue'
import DiceView from '@/modules/dice/DiceView.vue'
import SessionsView from '@/modules/sessions/SessionsView.vue'
import FactionsView from '@/modules/factions/FactionsView.vue'
import NpcsView from '@/modules/npcs/NpcsView.vue'
import WikiView from '@/modules/wiki/WikiView.vue'
import CombatView from '@/modules/combat/CombatView.vue'
import MapsView from '@/modules/maps/MapsView.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/health-check', name: 'health-check', component: HealthCheckView },
  { path: '/dice', name: 'dice', component: DiceView },
  { path: '/sessions', name: 'sessions', component: SessionsView },
  { path: '/factions', name: 'factions', component: FactionsView },
  { path: '/npcs', name: 'npcs', component: NpcsView },
  { path: '/wiki', name: 'wiki', component: WikiView },
  { path: '/combat', name: 'combat', component: CombatView },
  { path: '/maps', name: 'maps', component: MapsView },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
