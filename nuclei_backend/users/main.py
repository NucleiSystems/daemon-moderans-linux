from fastapi import APIRouter

users_router = APIRouter(prefix="/users")

from .auth_routes import *
from .user_handler import *
