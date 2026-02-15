from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
from contextlib import asynccontextmanager
import os

from database import init_db
from auth import router as auth_router
from user import router as user_router
from admin import router as admin_router
from tasks import router as tasks_router
from withdrawals import router as withdrawals_router
from support import router as support_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("=" * 60)
    print("🚀 SOCIAL PAY WEB APP")
    print("=" * 60)
    print("✅ Database initialized")
    print("✅ Server running")
    print("=" * 60)
    yield
    print("\n⚠️ Shutting down...")

app = FastAPI(
    title="Social Pay Web App",
    description="Complete earning platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

# API Routes
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(user_router, prefix="/api/user", tags=["User"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(withdrawals_router, prefix="/api/withdrawals", tags=["Withdrawals"])
app.include_router(support_router, prefix="/api/support", tags=["Support"])

# Web Pages
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    return templates.TemplateResponse("tasks.html", {"request": request})

@app.get("/wallet", response_class=HTMLResponse)
async def wallet_page(request: Request):
    return templates.TemplateResponse("wallet.html", {"request": request})

@app.get("/transfer", response_class=HTMLResponse)
async def transfer_page(request: Request):
    return templates.TemplateResponse("transfer.html", {"request": request})

@app.get("/withdrawal", response_class=HTMLResponse)
async def withdrawal_page(request: Request):
    return templates.TemplateResponse("withdrawal.html", {"request": request})

@app.get("/referrals", response_class=HTMLResponse)
async def referrals_page(request: Request):
    return templates.TemplateResponse("referrals.html", {"request": request})

@app.get("/admin-panel", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/support", response_class=HTMLResponse)
async def support_page(request: Request):
    return templates.TemplateResponse("support.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Social Pay API is running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)