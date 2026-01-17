from fastapi import FastAPI
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.services import router as services_router
from app.api.appointments import router as appointments_router # <--- 1. ИМПОРТ

app = FastAPI(title="Barbershop API Warsaw")

app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(services_router, prefix="/services", tags=["Services"])
app.include_router(appointments_router, prefix="/appointments", tags=["Appointments"]) # <--- 2. ПОДКЛЮЧЕНИЕ

@app.get("/")
def root():
    return {"message": "Serwer działa! 🇵🇱"}