import csv
from io import StringIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.crud.tagging_task import crud_tagging_task, serialize_task
from app.database import get_db
from app.schemas.tagging_task import (
    CreateTaggingTaskResponse,
    ImportTaggingTaskResponse,
    TaggingTaskDetailResponse,
    UpdateTaggingTaskCursorRequest,
    UpdateTaggingTaskItemRequest,
    UpdateTaggingTaskItemResponse,
    UpdateTaggingTaskResponse,
)

router = APIRouter(
    prefix="/tagging-tasks",
    tags=["tagging-tasks"],
    dependencies=[Depends(get_current_user)],
)

REQUIRED_COLUMNS = ("title", "summary", "category", "reason")


def serialize_item(item) -> dict:
    return {
        "id": item.id,
        "task_id": item.task_id,
        "row_index": item.row_index,
        "title": item.title,
        "summary": item.summary,
        "category": item.category,
        "reason": item.reason,
        "is_important": item.is_important,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def current_item_for(task):
    if not task.items:
        return None
    if task.current_index < 0 or task.current_index >= len(task.items):
        return None
    return task.items[task.current_index]


def parse_csv_rows(content: str) -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(content))
    fieldnames = reader.fieldnames or []
    missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing required columns: {', '.join(missing)}")

    rows: list[dict[str, str]] = []
    for index, row in enumerate(reader, start=1):
        normalized = {key: (value or "").strip() for key, value in row.items() if key}
        if not normalized.get("title"):
            raise HTTPException(status_code=422, detail=f"Row {index} has empty title")
        if not normalized.get("category"):
            raise HTTPException(status_code=422, detail=f"Row {index} has empty category")
        rows.append(normalized)

    if not rows:
        raise HTTPException(status_code=422, detail="CSV must contain at least one data row")
    return rows


@router.post("", response_model=CreateTaggingTaskResponse, status_code=201)
async def create_tagging_task(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="CSV must be UTF-8 encoded") from exc

    rows = parse_csv_rows(decoded)
    task = await crud_tagging_task.create_from_rows(
        db,
        original_file_name=file.filename or "tagging-task.csv",
        rows=rows,
    )
    current_item = current_item_for(task)
    return {
        "task": serialize_task(task),
        "current_item": serialize_item(current_item) if current_item else None,
    }


@router.get("/{task_id}", response_model=TaggingTaskDetailResponse)
async def get_tagging_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await crud_tagging_task.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tagging task not found")
    current_item = current_item_for(task)
    return {
        "task": serialize_task(task),
        "current_item": serialize_item(current_item) if current_item else None,
        "items": [serialize_item(item) for item in task.items],
    }


@router.get("", response_model=list[dict])
async def list_tagging_tasks(db: AsyncSession = Depends(get_db)):
    tasks = await crud_tagging_task.list_tasks(db)
    return [serialize_task(task) for task in tasks]


@router.patch("/{task_id}/cursor", response_model=UpdateTaggingTaskResponse)
async def update_tagging_task_cursor(
    task_id: int,
    body: UpdateTaggingTaskCursorRequest,
    db: AsyncSession = Depends(get_db),
):
    task = await crud_tagging_task.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tagging task not found")

    updated = await crud_tagging_task.update_cursor(db, task, body.current_index)
    current_item = current_item_for(updated)
    return {
        "task": serialize_task(updated),
        "current_item": serialize_item(current_item) if current_item else None,
    }


@router.patch("/{task_id}/items/{item_id}", response_model=UpdateTaggingTaskItemResponse)
async def update_tagging_task_item(
    task_id: int,
    item_id: int,
    body: UpdateTaggingTaskItemRequest,
    db: AsyncSession = Depends(get_db),
):
    task = await crud_tagging_task.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tagging task not found")

    item = await crud_tagging_task.get_item(db, task_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Tagging task item not found")

    updated_task, updated_item = await crud_tagging_task.update_item(
        db,
        task=task,
        item=item,
        is_important=body.is_important,
    )
    return {
        "task": serialize_task(updated_task),
        "item": serialize_item(updated_item),
    }


@router.post("/{task_id}/complete", response_model=UpdateTaggingTaskResponse)
async def complete_tagging_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await crud_tagging_task.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tagging task not found")
    if any(item.is_important is None for item in task.items):
        raise HTTPException(status_code=409, detail="All items must be labeled before completing the task")
    if task.status == "imported":
        raise HTTPException(status_code=409, detail="Imported task cannot be completed again")

    updated = await crud_tagging_task.complete(db, task)
    current_item = current_item_for(updated)
    return {
        "task": serialize_task(updated),
        "current_item": serialize_item(current_item) if current_item else None,
    }


@router.post("/{task_id}/import", response_model=ImportTaggingTaskResponse)
async def import_tagging_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await crud_tagging_task.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tagging task not found")
    if task.status != "completed":
        raise HTTPException(status_code=409, detail="Only completed tasks can be imported")

    updated_task, imported_count, skipped_count = await crud_tagging_task.import_examples(db, task)
    return {
        "task": serialize_task(updated_task),
        "imported_count": imported_count,
        "skipped_count": skipped_count,
    }
