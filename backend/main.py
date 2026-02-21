from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_tables
from routers import auth, groups, assignments, websocket

app = FastAPI(
    title="AI Ustoz Enterprise API",
    description="EdTech platform backend",
    version="1.0.0"
)

# CORS — Vercel frontend domeniga ruxsat
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.vercel.app",   # barcha vercel subdomain
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "*"  # development uchun, prod da o'zgartiring
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(assignments.router, prefix="/api")
app.include_router(websocket.router)

@app.on_event("startup")
async def startup():
    await create_tables()
    print("✅ AI Ustoz API ishga tushdi!")

@app.get("/")
async def root():
    return {"status": "ok", "app": "AI Ustoz Enterprise API", "version": "1.0.0"}

@app.get("/api/health")
async def health():
    return {"status": "ok"}
