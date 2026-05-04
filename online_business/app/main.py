from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.config import settings
from app.database import init_db
from app.routers import auth, users, products, orders, reviews, payments, analytics

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "DigitalMarket — a fully-featured digital products marketplace. "
        "Sellers list templates, ebooks, tools & courses. "
        "Platform earns 15% commission per sale + $29/month Pro subscriptions."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(reviews.router)
app.include_router(payments.router)
app.include_router(analytics.router)

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/dashboard", include_in_schema=False)
    def serve_dashboard():
        return FileResponse(os.path.join(frontend_dir, "dashboard.html"))


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.app_version}
