import { createApp } from 'vue'
import { VueQueryPlugin } from '@tanstack/vue-query'
import router from './router'
import App from './App.vue'
import { queryClient } from './shared/query/client'
import './styles/tokens.css'
import './styles/base.css'

const app = createApp(App)
app.use(VueQueryPlugin, { queryClient })
app.use(router)
app.mount('#app')
