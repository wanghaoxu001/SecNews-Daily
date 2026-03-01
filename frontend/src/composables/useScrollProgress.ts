import { ref, onMounted, onUnmounted } from 'vue'

export function useScrollProgress() {
  const progress = ref(0)

  function onScroll() {
    const scrollTop = document.documentElement.scrollTop || document.body.scrollTop
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight
    progress.value = scrollHeight > 0 ? Math.round((scrollTop / scrollHeight) * 100) : 0
  }

  onMounted(() => window.addEventListener('scroll', onScroll))
  onUnmounted(() => window.removeEventListener('scroll', onScroll))

  return { progress }
}
