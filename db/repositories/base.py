from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.base import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """Async CRUD + soft delete for models that inherit :class:`BaseModel`."""

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self._session = session
        self._model = model

    def _base_filter(self, stmt: Any, *, include_deleted: bool) -> Any:
        if not include_deleted:
            stmt = stmt.where(self._model.deleted_at.is_(None))
        return stmt

    async def get(
        self,
        pk: int,
        *,
        include_deleted: bool = False,
    ) -> ModelT | None:
        stmt = select(self._model).where(self._model.id == pk)
        stmt = self._base_filter(stmt, include_deleted=include_deleted)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> list[ModelT]:
        stmt = select(self._model).order_by(self._model.id.desc())
        stmt = self._base_filter(stmt, include_deleted=include_deleted)
        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *, include_deleted: bool = False) -> int:
        stmt = select(func.count()).select_from(self._model)
        stmt = self._base_filter(stmt, include_deleted=include_deleted)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def add(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def add_many(self, *entities: ModelT) -> tuple[ModelT, ...]:
        for e in entities:
            self._session.add(e)
        await self._session.flush()
        for e in entities:
            await self._session.refresh(e)
        return entities

    async def soft_delete(self, entity: ModelT) -> None:
        entity.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def soft_delete_by_id(self, pk: int) -> bool:
        entity = await self.get(pk, include_deleted=True)
        if entity is None or entity.deleted_at is not None:
            return False
        await self.soft_delete(entity)
        return True

    async def restore(self, entity: ModelT) -> None:
        entity.deleted_at = None
        await self._session.flush()

    async def restore_by_id(self, pk: int) -> bool:
        entity = await self.get(pk, include_deleted=True)
        if entity is None or entity.deleted_at is None:
            return False
        await self.restore(entity)
        return True

    async def hard_delete(self, entity: ModelT) -> None:
        self._session.delete(entity)
        await self._session.flush()

    async def update_by_id(self, pk: int, **values: Any) -> bool:
        if not values:
            return False
        stmt = (
            update(self._model)
            .where(self._model.id == pk, self._model.deleted_at.is_(None))
            .values(**values)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0
