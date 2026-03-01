import time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.crud.llm_config import crud_llm_config, ALL_TASK_TYPES
from app.schemas.llm_config import LlmConfigCreate, LlmConfigUpdate, LlmConfigResponse, LlmTestResponse

router = APIRouter(prefix="/llm-configs", tags=["llm-configs"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[LlmConfigResponse])
async def list_configs(db: AsyncSession = Depends(get_db)):
    items, _ = await crud_llm_config.get_multi(db, offset=0, limit=100)
    return items


@router.post("/ensure-defaults", response_model=list[LlmConfigResponse])
async def ensure_defaults(db: AsyncSession = Depends(get_db)):
    """Ensure all task-type configs exist, creating missing ones with empty fields."""
    return await crud_llm_config.ensure_all_task_types(db)


@router.post("/test/{task_type}", response_model=LlmTestResponse)
async def test_config(task_type: str, db: AsyncSession = Depends(get_db)):
    """Test LLM connectivity for the given task_type using its resolved config."""
    resolved = await crud_llm_config.get_resolved(db, task_type)
    if not resolved:
        raise HTTPException(status_code=404, detail="LLM config not found")

    base_url = resolved.get("base_url")
    api_key = resolved.get("api_key")
    model = resolved.get("model")

    if not base_url or not model:
        raise HTTPException(status_code=400, detail="base_url 和 model 不能为空")

    base_url = base_url.rstrip("/")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if task_type == "embedding":
                resp = await client.post(
                    f"{base_url}/v1/embeddings",
                    headers=headers,
                    json={"model": model, "input": "test"},
                )
            else:
                resp = await client.post(
                    f"{base_url}/v1/chat/completions",
                    headers=headers,
                    json={"model": model, "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5},
                )
            latency_ms = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                return LlmTestResponse(success=True, message="连接成功", latency_ms=latency_ms)
            else:
                detail = resp.text[:200]
                return LlmTestResponse(success=False, message=f"HTTP {resp.status_code}: {detail}", latency_ms=latency_ms)
    except httpx.TimeoutException:
        latency_ms = int((time.time() - start) * 1000)
        return LlmTestResponse(success=False, message="连接超时（15s）", latency_ms=latency_ms)
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return LlmTestResponse(success=False, message=f"连接失败: {str(e)}", latency_ms=latency_ms)


@router.get("/{config_id}", response_model=LlmConfigResponse)
async def get_config(config_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_llm_config.get(db, config_id)
    if not obj:
        raise HTTPException(status_code=404, detail="LLM config not found")
    return obj


@router.get("/task/{task_type}")
async def get_resolved_config(task_type: str, db: AsyncSession = Depends(get_db)):
    result = await crud_llm_config.get_resolved(db, task_type)
    if not result:
        raise HTTPException(status_code=404, detail="LLM config not found")
    return result


@router.post("", response_model=LlmConfigResponse, status_code=201)
async def create_config(body: LlmConfigCreate, db: AsyncSession = Depends(get_db)):
    return await crud_llm_config.create(db, obj_in=body)


@router.put("/{config_id}", response_model=LlmConfigResponse)
async def update_config(config_id: int, body: LlmConfigUpdate, db: AsyncSession = Depends(get_db)):
    obj = await crud_llm_config.get(db, config_id)
    if not obj:
        raise HTTPException(status_code=404, detail="LLM config not found")
    return await crud_llm_config.update(db, db_obj=obj, obj_in=body)


@router.delete("/{config_id}", status_code=204)
async def delete_config(config_id: int, db: AsyncSession = Depends(get_db)):
    obj = await crud_llm_config.get(db, config_id)
    if not obj:
        raise HTTPException(status_code=404, detail="LLM config not found")
    if obj.task_type in ALL_TASK_TYPES:
        raise HTTPException(status_code=400, detail=f"Cannot delete built-in config '{obj.task_type}'")
    deleted = await crud_llm_config.delete(db, id=config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="LLM config not found")
