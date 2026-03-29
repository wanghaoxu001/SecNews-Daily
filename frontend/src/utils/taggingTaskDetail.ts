import type { TaggingTaskDetailResponse, TaggingTaskItem, TaggingTaskListItem, UpdateTaggingTaskItemResponse } from '../types'

export function createTaggingTaskDetail(task: TaggingTaskListItem, currentItem: TaggingTaskItem | null): TaggingTaskDetailResponse {
  return {
    task,
    current_item: currentItem,
    items: currentItem ? [currentItem] : [],
  }
}

export function applyUpdatedTaggingTaskItem(
  detail: TaggingTaskDetailResponse,
  result: UpdateTaggingTaskItemResponse,
): TaggingTaskDetailResponse {
  const existingItems = detail.items ?? []
  const hasItem = existingItems.some((item) => item.id === result.item.id)
  const nextItems = hasItem
    ? existingItems.map((item) => (item.id === result.item.id ? result.item : item))
    : [...existingItems, result.item].sort((left, right) => left.row_index - right.row_index)
  const nextCurrentItem = nextItems.find((item) => item.id === result.item.id) ?? result.item

  return {
    task: result.task,
    current_item: nextCurrentItem,
    items: nextItems,
  }
}
