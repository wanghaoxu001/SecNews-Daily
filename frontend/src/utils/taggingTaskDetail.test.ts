import { describe, expect, it } from 'vitest'
import type { TaggingTaskItem, TaggingTaskListItem, UpdateTaggingTaskItemResponse } from '../types'
import { applyUpdatedTaggingTaskItem, createTaggingTaskDetail } from './taggingTaskDetail'

function makeTask(overrides: Partial<TaggingTaskListItem> = {}): TaggingTaskListItem {
  return {
    id: 1,
    original_file_name: 'sample.csv',
    status: 'in_progress',
    total_count: 2,
    current_index: 0,
    labeled_count: 0,
    imported_at: null,
    created_at: '2026-03-29T00:00:00Z',
    updated_at: '2026-03-29T00:00:00Z',
    ...overrides,
  }
}

function makeItem(overrides: Partial<TaggingTaskItem> = {}): TaggingTaskItem {
  return {
    id: 11,
    task_id: 1,
    row_index: 0,
    title: '标题',
    summary: '摘要',
    category: '重大漏洞风险提示',
    reason: '原因',
    is_important: null,
    created_at: '2026-03-29T00:00:00Z',
    updated_at: '2026-03-29T00:00:00Z',
    ...overrides,
  }
}

describe('taggingTaskDetail utils', () => {
  it('creates a complete detail shape from create-task response payload', () => {
    const currentItem = makeItem()

    expect(createTaggingTaskDetail(makeTask(), currentItem)).toEqual({
      task: makeTask(),
      current_item: currentItem,
      items: [currentItem],
    })
  })

  it('updates the current item even when the initial detail only has the create-task shape', () => {
    const initialItem = makeItem({ is_important: null })
    const detail = createTaggingTaskDetail(makeTask(), initialItem)
    const updatedItem = makeItem({ is_important: true, updated_at: '2026-03-29T00:01:00Z' })
    const updateResult: UpdateTaggingTaskItemResponse = {
      task: makeTask({ labeled_count: 1, updated_at: '2026-03-29T00:01:00Z' }),
      item: updatedItem,
    }

    expect(applyUpdatedTaggingTaskItem(detail, updateResult)).toEqual({
      task: updateResult.task,
      current_item: updatedItem,
      items: [updatedItem],
    })
  })
})
