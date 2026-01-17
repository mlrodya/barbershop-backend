from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.deps import get_current_user # <-- Добавить этот импорт
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.security import get_password_hash

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Проверяем, есть ли уже такой email
    query = select(User).where(User.email == user_in.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким email уже существует"
        )

    # 2. Создаем нового пользователя
    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password), # Хешируем!
        full_name=user_in.full_name,
        phone=user_in.phone,
        role="client" # По умолчанию все - клиенты
    )

    # 3. Сохраняем в БД
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
# ... старый код create_user ...

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Возвращает профиль текущего пользователя.
    Доступно только с валидным токеном!
    """
    return current_user