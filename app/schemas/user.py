from pydantic import BaseModel, EmailStr

# Базовая схема (общие поля)
class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None

# Схема для СОЗДАНИЯ пользователя (то, что присылает клиент)
class UserCreate(UserBase):
    password: str

# Схема для ОТВЕТА (то, что мы отдаем клиенту - пароль скрываем!)
class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool

    class Config:
        from_attributes = True # Важно для работы с ORM