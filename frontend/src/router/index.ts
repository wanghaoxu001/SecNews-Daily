import { createRouter, createWebHistory } from 'vue-router'
import { setupGuards } from './guards'

const routes = [
  {
    path: '/',
    redirect: '/today',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/today',
    name: 'TodayNews',
    component: () => import('../views/TodayNewsView.vue'),
  },
  {
    path: '/briefings',
    name: 'BriefingList',
    component: () => import('../views/BriefingListView.vue'),
  },
  {
    path: '/briefings/:id',
    name: 'BriefingEdit',
    component: () => import('../views/BriefingEditView.vue'),
  },
  {
    path: '/management',
    name: 'Management',
    component: () => import('../views/ManagementView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

setupGuards(router)

export default router
