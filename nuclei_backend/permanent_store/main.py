from fastapi import APIRouter

from . import permanent_store_model

permanent_store_router = APIRouter(prefix="/storage")


from . import permanent_store_routes
