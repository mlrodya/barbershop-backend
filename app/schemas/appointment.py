from pydantic import BaseModel
from datetime import datetime

# Базовая схема
class AppointmentBase(BaseModel):
    service_id: int
    time_start: datetime  # Формат: 2025-01-11T14:00:00

# То, что присылает клиент при записи
class AppointmentCreate(AppointmentBase):
    pass

# То, что мы отдаем в ответ (с ID и статусом)
class AppointmentResponse(AppointmentBase):
    id: int
    client_id: int
    status: str # pending / confirmed

    class Config:
        from_attributes = True