from sqlalchemy.ext.asyncio import AsyncSession

from db.models.item import Item
from db.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Item)
