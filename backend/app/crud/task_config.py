from app.crud.base import CRUDBase
from app.models.task_config import TaskConfig
from app.schemas.task_config import TaskConfigCreate, TaskConfigUpdate

crud_task_config = CRUDBase[TaskConfig, TaskConfigCreate, TaskConfigUpdate](TaskConfig)
