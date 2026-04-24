import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for app startup and shutdown."""
    # Startup — schema is managed by Alembic migrations.
    logger.info("Starting Pizza Striker Backend...")
    yield
    # Shutdown
    logger.info("Shutting down Pizza Striker Backend...")


# Create FastAPI app
app = FastAPI(
    title="Pizza Striker API",
    description="API for gamified office strike tracking system",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Pizza Striker API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# TODO: Add routers
# from app.auth.router import router as auth_router
# from app.users.router import router as users_router
# from app.strikes.router import router as strikes_router
# from app.pizza_events.router import router as pizza_events_router
# from app.notifications.router import router as notifications_router
# from app.admin.users_router import router as admin_users_router
# from app.admin.strikes_router import router as admin_strikes_router
# from app.admin.events_router import router as admin_events_router
# from app.admin.dashboard_router import router as admin_dashboard_router

# app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
# app.include_router(strikes_router, prefix="/api/v1/strikes", tags=["strikes"])
# app.include_router(pizza_events_router, prefix="/api/v1/pizza-events", tags=["pizza-events"])
# app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])
# app.include_router(admin_users_router, prefix="/api/v1/admin/users", tags=["admin-users"])
# app.include_router(admin_strikes_router, prefix="/api/v1/admin/strikes", tags=["admin-strikes"])
# app.include_router(admin_events_router, prefix="/api/v1/admin/pizza-events", tags=["admin-pizza-events"])
# app.include_router(admin_dashboard_router, prefix="/api/v1/admin/dashboard", tags=["admin-dashboard"])
