import base64
import asyncio
from concurrent.futures import ThreadPoolExecutor

import httpx
from celery import Celery
from fastapi import BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from nuclei_backend.users.auth_utils import get_current_user
from ...users.user_handler_utils import get_db
from ..CompressionBase import CompressionImpl
from ..ipfs_utils import *
from ..main import storage_service
from .image_compression_utils import CompressImage


# celery_app = Celery(
#     __name__,
#     broker="amqp://myuser:mypassword@host.docker.internal:5672",
#     backend="rpc://",
# )


import threading


lock = threading.Lock()


# @celery_app.task(bind=True)
def process_file(
    file: bytes, filename: str, ipfs_flag: bool, identity_token: str, db
) -> None:
    try:
        with lock:
            compressing_file = CompressImage(file, filename)
            print("files compressed")
            compressed_file = compressing_file.produce_compression()
            if ipfs_flag:
                print("before ipfs flag")
                try:
                    ipfs_cid = compressing_file.commit_to_ipfs(
                        compressed_file, filename, identity_token, db
                    )
                except Exception as e:
                    print(f"the error was {e}")
                print(f"IPFS CID for {filename}: {ipfs_cid}")
            compressing_file.cleanup_compression_outcome()
    except Exception as e:
        print(f"Error compressing and storing file {filename}: {str(e)}")


3


def process_files(
    files: List[UploadFile],
    ipfs_flag: bool | None = True,
    identity_token: str = Depends(get_current_user),
    db=Depends(get_db),
):
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for file in files:
            _file = file.file
            _file = _file.read()
            _filename = file.filename
            future = executor.submit(
                process_file, _file, _filename, ipfs_flag, identity_token, db
            )
            futures.append(future)

        results = [future.result() for future in futures]

    return results


@storage_service.post("/compress/image")
async def compress_task_image(
    files: List[UploadFile],
    background_tasks: BackgroundTasks,
    ipfs_flag: bool | None = True,
    identity_token: str = Depends(get_current_user),
    db=Depends(get_db),
):
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file uploaded",
        )
    try:
        background_tasks.add_task(process_files, files, ipfs_flag, identity_token, db)

        return {"message": "Files submitted for compression"}, status.HTTP_202_ACCEPTED
    except Exception as e:
        return {"error": e}
