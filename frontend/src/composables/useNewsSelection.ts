import { ref } from 'vue'
import { todayInChina } from '../utils/date'

export function useNewsSelection() {
  const today = todayInChina()
  const storageKey = `news_selection_${today}`

  const selectedIds = ref<Set<number>>(new Set(
    JSON.parse(localStorage.getItem(storageKey) || '[]')
  ))

  function toggle(id: number) {
    if (selectedIds.value.has(id)) {
      selectedIds.value.delete(id)
    } else {
      selectedIds.value.add(id)
    }
    save()
  }

  function isSelected(id: number): boolean {
    return selectedIds.value.has(id)
  }

  function save() {
    localStorage.setItem(storageKey, JSON.stringify([...selectedIds.value]))
  }

  function getSelectedIds(): number[] {
    return [...selectedIds.value]
  }

  function clear() {
    selectedIds.value.clear()
    save()
  }

  return { selectedIds, toggle, isSelected, getSelectedIds, clear }
}
