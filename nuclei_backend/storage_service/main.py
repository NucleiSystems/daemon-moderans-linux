from fastapi import APIRouter

storage_service = APIRouter(prefix="/storage")

from .image_compression.image_compression_routes import *
from .ipfs_routes import *
from .misc_compression.misc_compression_routes import *
