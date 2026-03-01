from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.crud.processing_config import crud_processing_config
from app.schemas.processing_config import ProcessingConfigCreate, ProcessingConfigUpdate, ProcessingConfigResponse

router = APIRouter(prefix="/processing-configs", tags=["processing-configs"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ProcessingConfigResponse])
async def list_configs(db: AsyncSession = Depends(get_db)):
    items, _ = await crud_processing_config.get_multi(db, offset=0, limit=100)
    return items


@router.get("/{config_id}", response_model=ProcessingConfigResponse)
async def get_config(config_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_processing_config.get(db, config_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Processing config not found")
    return obj


@router.post("", response_model=ProcessingConfigResponse, status_code=201)
async def create_config(body: ProcessingConfigCreate, db: AsyncSession = Depends(get_db)):
    return await crud_processing_config.create(db, obj_in=body)


@router.put("/{config_id}", response_model=ProcessingConfigResponse)
async def update_config(config_id: int, body: ProcessingConfigUpdate, db: AsyncSession = Depends(get_db)):
    obj = await crud_processing_config.get(db, config_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Processing config not found")
    return await crud_processing_config.update(db, db_obj=obj, obj_in=body)


@router.delete("/{config_id}", status_code=204)
async def delete_config(config_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await crud_processing_config.delete(db, id=config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Processing config not found")
