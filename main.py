import os
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.adminRoutes import adminRoutes

app = FastAPI(title="Text To Speech Service")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)

OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/audio", StaticFiles(directory=OUTPUT_DIR), name="audio")

app.include_router(adminRoutes)

# uvicorn main:app --reload --port 8000  // to run the application