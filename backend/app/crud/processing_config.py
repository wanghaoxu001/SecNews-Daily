from app.crud.base import CRUDBase
from app.models.processing_config import ProcessingConfig
from app.schemas.processing_config import ProcessingConfigCreate, ProcessingConfigUpdate

crud_processing_config = CRUDBase[ProcessingConfig, ProcessingConfigCreate, ProcessingConfigUpdate](ProcessingConfig)
