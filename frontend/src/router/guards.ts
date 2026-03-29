import type { Router } from 'vue-router'

export function setupGuards(router: Router) {
  const publicRouteNames = new Set(['Login'])

  router.beforeEach((to, _from, next) => {
    const token = localStorage.getItem('token')
    const routeName = String(to.name ?? '')
    const isPublicRoute = publicRouteNames.has(routeName)

    if (!isPublicRoute && !token) {
      next({ name: 'Login' })
    } else if (routeName === 'Login' && token) {
      next({ name: 'TodayNews' })
    } else {
      next()
    }
  })
}
