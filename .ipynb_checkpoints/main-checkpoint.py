from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.routers.adminRoutes import adminRoutes

app = FastAPI(title="Text To Speech Service")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(adminRoutes)

# uvicorn main:app --reload --port 8000  // to run the application