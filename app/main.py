from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <--- Импорт
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.services import router as services_router
from app.api.appointments import router as appointments_router

app = FastAPI(title="Barbershop API")

# 👇 НАСТРОЙКА CORS (РАЗРЕШЕНИЕ ДЛЯ ФРОНТЕНДА)
origins = [
    "http://localhost:3000",  # React / Next.js
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Vite
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Пока разрешаем ВСЕМ (для удобства разработки)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(services_router, prefix="/services", tags=["Services"])
app.include_router(appointments_router, prefix="/appointments", tags=["Appointments"])

@app.get("/")
async def root():
    return {"message": "Welcome to Barbershop API"}