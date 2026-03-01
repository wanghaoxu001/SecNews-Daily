import type { Router } from 'vue-router'

export function setupGuards(router: Router) {
  router.beforeEach((to, _from, next) => {
    const token = localStorage.getItem('token')
    if (to.name !== 'Login' && !token) {
      next({ name: 'Login' })
    } else if (to.name === 'Login' && token) {
      next({ name: 'TodayNews' })
    } else {
      next()
    }
  })
}
