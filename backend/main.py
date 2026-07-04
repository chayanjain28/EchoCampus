import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database.connection import engine, Base
from backend.routes import auth, complaints, feedback, notifications, analytics

# Create all database tables
Base.metadata.create_all(bind=engine)

# Auto-seed demo data on first run (only if no orgs exist)
def auto_seed():
    from backend.database.connection import SessionLocal
    from backend.models.models import Organization
    db = SessionLocal()
    try:
        count = db.query(Organization).count()
        if count == 0:
            print("[SEED] No organizations found. Running auto-seed...")
            from backend.seed import main as seed_main
            seed_main()
            print("[SEED] Done.")
    except Exception as e:
        print(f"[SEED] Skipped: {e}")
    finally:
        db.close()

auto_seed()

app = FastAPI(
    title="EchoCampus AI API",
    description="Backend API for EchoCampus AI - Student Welfare & Campus Intelligence Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS — allow all origins (update with your Vercel URL in production)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uploads directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Routers
app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(feedback.router)
app.include_router(notifications.router)
app.include_router(analytics.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "EchoCampus AI",
        "version": "2.0.0",
        "message": "Every Student Voice, Intelligently Heard.",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
