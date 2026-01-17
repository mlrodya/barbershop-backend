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
from app.api.deps import get_current_user

router = APIRouter()

# --- КОНСТАНТЫ РАБОЧЕГО ДНЯ ---
WORK_START_HOUR = 10  # Открываемся в 10:00
WORK_END_HOUR = 20    # Закрываемся в 20:00

@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_in: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Создать запись (с проверкой накладок)"""
    # 1. Получаем услугу
    result = await db.execute(select(Service).where(Service.id == appointment_in.service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Usługa nie znaleziona")

    # 2. Считаем интервал новой записи
    start_time = appointment_in.time_start
    end_time = start_time + timedelta(minutes=service.duration_minutes)

    # Проверка: Попадаем ли в рабочее время?
    if start_time.hour < WORK_START_HOUR or end_time.hour > WORK_END_HOUR or (end_time.hour == WORK_END_HOUR and end_time.minute > 0):
         raise HTTPException(status_code=400, detail="Barbershop jest zamknięty w tych godzinach (Мы закрыты)")

    # 3. Проверяем накладки с другими записями
    # Берем все записи на этот день
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
        # Если интервалы пересекаются
        if start_time < existing_end and end_time > existing.time_start:
             raise HTTPException(status_code=400, detail="Ten termin jest już zajęty (Занято)")

    # 4. Сохраняем
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


# 👇 НОВЫЙ ЭНДПОИНТ: СВОБОДНЫЕ СЛОТЫ
@router.get("/slots/")
async def get_available_slots(
    service_id: int,
    check_date: date,
    db: AsyncSession = Depends(get_db)
):
    """
    Показать доступные часы для записи на конкретную дату.
    """
    # 1. Узнаем длительность услуги
    result = await db.execute(select(Service).where(Service.id == service_id))
    service = result.scalars().first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    duration = timedelta(minutes=service.duration_minutes)

    # 2. Загружаем все записи на этот день
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

    # 3. Генерируем слоты (каждые 30 минут)
    available_slots = []
    
    # Начинаем рабочий день
    current_slot = datetime.combine(check_date, datetime.min.time()).replace(hour=WORK_START_HOUR)
    work_end = current_slot.replace(hour=WORK_END_HOUR)

    while current_slot + duration <= work_end:
        slot_end = current_slot + duration
        is_free = True

        # Проверяем, не пересекается ли слот с существующими записями
        for appt in appointments:
            appt_end = appt.time_start + timedelta(minutes=appt.service.duration_minutes)
            if current_slot < appt_end and slot_end > appt.time_start:
                is_free = False
                break
        
        if is_free:
            available_slots.append(current_slot.strftime("%H:%M"))

        # Шаг сетки расписания - 30 минут
        current_slot += timedelta(minutes=30)

    return {"date": check_date, "available_slots": available_slots}