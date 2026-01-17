from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from datetime import datetime, timedelta, date

from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.api.deps import get_current_user, get_current_admin  # <--- Добавили Admin

router = APIRouter()

# --- КОНСТАНТЫ РАБОЧЕГО ДНЯ ---
WORK_START_HOUR = 10
WORK_END_HOUR = 20

# 1. СОЗДАНИЕ ЗАПИСИ
@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_in: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать запись (с проверкой накладок)"""
    result = await db.execute(select(Service).where(Service.id == appointment_in.service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Usługa nie znaleziona")

    start_time = appointment_in.time_start
    end_time = start_time + timedelta(minutes=service.duration_minutes)

    if start_time.hour < WORK_START_HOUR or end_time.hour > WORK_END_HOUR:
         raise HTTPException(status_code=400, detail="Barbershop jest zamknięty")

    day_start = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    
    query = select(Appointment).join(Service).where(
        and_(
            Appointment.time_start >= day_start,
            Appointment.time_start < day_end,
            Appointment.status != "cancelled"
        )
    )
    result = await db.execute(query)
    existing_appointments = result.scalars().all()

    for existing in existing_appointments:
        existing_end = existing.time_start + timedelta(minutes=existing.service.duration_minutes)
        if start_time < existing_end and end_time > existing.time_start:
             raise HTTPException(status_code=400, detail="Ten termin jest już zajęty")

    new_appointment = Appointment(
        client_id=current_user.id,
        service_id=appointment_in.service_id,
        time_start=start_time,
        status="confirmed"
    )
    db.add(new_appointment)
    await db.commit()
    await db.refresh(new_appointment)
    return new_appointment

# 2. СВОБОДНЫЕ СЛОТЫ (Для всех)
@router.get("/slots/")
async def get_available_slots(
    service_id: int,
    check_date: date,
    db: AsyncSession = Depends(get_db)
):
    """Показать доступные часы"""
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    duration = timedelta(minutes=service.duration_minutes)
    day_start = datetime.combine(check_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    query = select(Appointment).join(Service).where(
        and_(
            Appointment.time_start >= day_start,
            Appointment.time_start < day_end,
            Appointment.status != "cancelled"
        )
    )
    result = await db.execute(query)
    appointments = result.scalars().all()

    available_slots = []
    current_slot = datetime.combine(check_date, datetime.min.time()).replace(hour=WORK_START_HOUR)
    work_end = current_slot.replace(hour=WORK_END_HOUR)

    while current_slot + duration <= work_end:
        slot_end = current_slot + duration
        is_free = True
        for appt in appointments:
            appt_end = appt.time_start + timedelta(minutes=appt.service.duration_minutes)
            if current_slot < appt_end and slot_end > appt.time_start:
                is_free = False
                break
        if is_free:
            available_slots.append(current_slot.strftime("%H:%M"))
        current_slot += timedelta(minutes=30)

    return {"date": check_date, "available_slots": available_slots}

# 👇 3. АДМИНКА: ВСЕ ЗАПИСИ (Только для Админа)
@router.get("/admin/", response_model=list[AppointmentResponse])
async def get_all_appointments_admin(
    check_date: date,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin) # <--- Фейсконтроль
):
    """
    Показать все записи на выбранный день.
    Только для роли 'admin'.
    """
    day_start = datetime.combine(check_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)

    # Загружаем записи + данные клиента (join User)
    query = select(Appointment).where(
        and_(
            Appointment.time_start >= day_start,
            Appointment.time_start < day_end
        )
    ).order_by(Appointment.time_start) # Сортируем по времени
    
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    return appointments