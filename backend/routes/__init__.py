from fastapi import APIRouter

# Create main router
router = APIRouter()

# Import and include API routes after router creation to avoid circular imports
from . import api
router.include_router(api.router, prefix="/api")

# Make router available when importing from routes package
__all__ = ['router']
