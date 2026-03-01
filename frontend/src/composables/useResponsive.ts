import { computed, onMounted, onUnmounted, ref } from 'vue'

const MOBILE_BREAKPOINT = 768
const TABLET_BREAKPOINT = 1024

export function useResponsive() {
  const width = ref(typeof window === 'undefined' ? 1280 : window.innerWidth)

  function onResize() {
    width.value = window.innerWidth
  }

  onMounted(() => {
    width.value = window.innerWidth
    window.addEventListener('resize', onResize, { passive: true })
  })

  onUnmounted(() => {
    window.removeEventListener('resize', onResize)
  })

  const isMobile = computed(() => width.value < MOBILE_BREAKPOINT)
  const isTablet = computed(() => width.value >= MOBILE_BREAKPOINT && width.value < TABLET_BREAKPOINT)
  const isDesktop = computed(() => width.value >= TABLET_BREAKPOINT)

  return {
    width,
    isMobile,
    isTablet,
    isDesktop,
  }
}
