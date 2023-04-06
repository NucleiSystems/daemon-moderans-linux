import base64

import httpx
from fastapi import BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from concurrent.futures import ProcessPoolExecutor
from typing import List
from functools import partial

from nuclei_backend.users.auth_utils import get_current_user

from ...users.user_handler_utils import get_db
from ..CompressionBase import CompressionImpl
from ..ipfs_utils import *
from ..main import storage_service
from .image_compression_utils import CompressImage, ImageCompressionTask
from multiprocessing import Process

# https://stackoverflow.com/questions/70043665/fastapi-unvicorn-request-hanging-during-invocation-of-call-next-path-operation


from celery import Celery

app = Celery(
    "compress_task_image",
    broker="amqp://user:password@rabbitmq//",
    backend="rpc://",
)


@app.task
async def compress_and_store_task(
    file: bytes,
    filename: str,
    ipfs_flag: bool,
    identity_token: str,
    db,
) -> None:
    try:
        compressing_file = CompressImage(file, filename)

        compressed_file = compressing_file.produce_compression()
        if ipfs_flag:
            ipfs_cid = await compressing_file.commit_to_ipfs(
                compressed_file, filename, identity_token, db
            )
            print(f"IPFS CID for {filename}: {ipfs_cid}")
        compressing_file.cleanup_compression_outcome()
    except Exception as e:
        print(f"Error compressing and storing file {filename}: {str(e)}")


@app.task
async def process_files_task(
    files: List[UploadFile],
    ipfs_flag: bool,
    identity_token: str,
    db,
) -> None:
    tasks = []
    for file in files:
        _file = file.file.read()
        _filename = file.filename

        if identity_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized user",
            )
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded",
            )

        tasks.append(
            compress_and_store_task.s(
                file=_file,
                filename=_filename,
                ipfs_flag=ipfs_flag,
                identity_token=identity_token,
                db=db,
            )
        )

    # Enqueue tasks in the Celery app
    await asyncio.gather(*[task() for task in tasks])


@storage_service.post("/compress/image")
async def compress_task_image(
    files: List[UploadFile],
    background: BackgroundTasks,
    ipfs_flag: bool | None = True,
    identity_token: str = Depends(get_current_user),
    db=Depends(get_db),
):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded",
        )

    # Enqueue task to Celery app
    process_files_task.delay(files, ipfs_flag, identity_token, db)

    return {"message": "Successfully compressed image"}, status.HTTP_200_OK
