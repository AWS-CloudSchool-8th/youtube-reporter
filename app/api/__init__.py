# app/api/__init__.py
from .youtube import router as youtube_router

__all__ = ["youtube_router"]