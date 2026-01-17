from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text
from app.db.session import Base

class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True) # Название (Стрижка)
    price: Mapped[int] = mapped_column(Integer) # Цена (например, 2000)
    duration_minutes: Mapped[int] = mapped_column(Integer) # Длительность (30 мин)
    description: Mapped[str] = mapped_column(Text, nullable=True) # Описание