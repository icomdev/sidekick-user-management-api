import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.base.config.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    entra_object_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )
