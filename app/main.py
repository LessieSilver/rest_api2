from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import init_db
from app.routers import auth, user, advertisement


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Advertisements Service",
    description="Сервис объявлений купли/продажи с JWT-авторизацией",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(advertisement.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Advertisements API is running"}
