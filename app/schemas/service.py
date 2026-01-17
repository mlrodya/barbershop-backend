from pydantic import BaseModel

# Базовый класс (общие поля)
class ServiceBase(BaseModel):
    name: str
    price: int
    duration_minutes: int
    description: str | None = None

# То, что присылает пользователь при создании
class ServiceCreate(ServiceBase):
    pass

# То, что мы отдаем в ответе (добавляем ID)
class ServiceResponse(ServiceBase):
    id: int

    class Config:
        from_attributes = True