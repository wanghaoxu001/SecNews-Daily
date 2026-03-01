from app.crud.base import CRUDBase
from app.models.rss_source import RssSource
from app.schemas.rss_source import RssSourceCreate, RssSourceUpdate

crud_rss_source = CRUDBase[RssSource, RssSourceCreate, RssSourceUpdate](RssSource)
