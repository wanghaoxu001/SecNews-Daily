from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.crud.importance_example import crud_importance_example
from app.schemas.importance_example import (
    ImportanceExampleCreate,
    ImportanceExampleUpdate,
    ImportanceExampleResponse,
)

router = APIRouter(
    prefix="/importance-examples",
    tags=["importance-examples"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[ImportanceExampleResponse])
async def list_examples(
    category: str | None = None, page: int = 1, page_size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    if category:
        items = await crud_importance_example.get_by_category(db, category)
        return items
    items, _ = await crud_importance_example.get_multi(db, offset=(page - 1) * page_size, limit=page_size)
    return items


@router.get("/{example_id}", response_model=ImportanceExampleResponse)
async def get_example(example_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_importance_example.get(db, example_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Importance example not found")
    return obj


@router.post("", response_model=ImportanceExampleResponse, status_code=201)
async def create_example(body: ImportanceExampleCreate, db: AsyncSession = Depends(get_db)):
    return await crud_importance_example.create(db, obj_in=body)


@router.post("/bulk-import", response_model=list[ImportanceExampleResponse], status_code=201)
async def bulk_import(items: list[ImportanceExampleCreate], db: AsyncSession = Depends(get_db)):
    return await crud_importance_example.bulk_create(db, items)


@router.put("/{example_id}", response_model=ImportanceExampleResponse)
async def update_example(example_id: int, body: ImportanceExampleUpdate, db: AsyncSession = Depends(get_db)):
    obj = await crud_importance_example.get(db, example_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Importance example not found")
    return await crud_importance_example.update(db, db_obj=obj, obj_in=body)


@router.delete("/{example_id}", status_code=204)
async def delete_example(example_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud_importance_example.delete(db, id=example_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Importance example not found")
