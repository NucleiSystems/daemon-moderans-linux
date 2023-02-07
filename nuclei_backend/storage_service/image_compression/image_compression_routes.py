import base64

import httpx
from fastapi import Depends, File, HTTPException, UploadFile, status

from nuclei_backend.users.auth_utils import get_current_user

from ...users.user_handler_utils import get_db
from ..CompressionBase import CompressionImpl
from ..ipfs_utils import *
from ..main import storage_service
from .image_compression_utils import CompressImage

# https://stackoverflow.com/questions/70043665/fastapi-unvicorn-request-hanging-during-invocation-of-call-next-path-operation


@storage_service.post("/compress/image")
async def compress_task_image(
    files: List[UploadFile],
    ipfs_flag: bool | None = True,
    identity_token: str = Depends(get_current_user),
    db=Depends(get_db),
):
    for file in files:
        _file = file.file
        _file = _file.read()
        _filename = file.filename

        if identity_token is None:
            return {"message": "Unauthorized user"}, status.HTTP_401_UNAUTHORIZED
        if not file:
            return {"error": "No file uploaded"}

        compressing_file = CompressImage(_file, _filename)

        compressed_file = compressing_file.produce_compression()
        if ipfs_flag:
            compressing_file.commit_to_ipfs(
                compressed_file, _filename, identity_token, db
            )
        compressing_file.cleanup_compression_outcome()
    return {"message": "Successfully compressed video"}, status.HTTP_200_OK
