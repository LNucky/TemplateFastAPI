from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import BaseModel


class Item(BaseModel):
    __tablename__ = "items"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
