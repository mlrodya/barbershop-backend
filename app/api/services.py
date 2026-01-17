from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models.service import Service
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceResponse
from app.api.deps import get_current_admin  # <--- Импортируем охрану

router = APIRouter()

# 1. Создание услуги - ТОЛЬКО АДМИН
@router.post("/", response_model=ServiceResponse)
async def create_service(
    service: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin) # <--- Защита включена
):
    """
    Dodaj nową usługę (Tylko Admin).
    """
    new_service = Service(
        name=service.name,
        price=service.price,
        duration_minutes=service.duration_minutes,
        description=service.description
    )
    db.add(new_service)
    await db.commit()
    await db.refresh(new_service)
    return new_service

# 2. Просмотр списка - ДЛЯ ВСЕХ (Защиты нет)
@router.get("/", response_model=list[ServiceResponse])
async def read_services(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista usług (Dostępne dla wszystkich).
    """
    result = await db.execute(select(Service).offset(skip).limit(limit))
    services = result.scalars().all()
    return services