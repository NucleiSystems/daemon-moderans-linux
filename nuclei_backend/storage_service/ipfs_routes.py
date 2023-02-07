from __future__ import annotations

import contextlib
import datetime
import hashlib
import logging
import os
import pathlib
from fileinput import filename
from subprocess import PIPE, Popen, call
from typing import *
from uuid import UUID, uuid4

import gevent
import sqlalchemy.exc
from fastapi import Depends, HTTPException, UploadFile

# from nuclei_backend.users.auth_utils import get_current_user
from nuclei_backend.users.user_models import User

from ..users.auth_utils import get_current_user
from ..users.user_handler_utils import get_db
from .config import Config
from .ipfs_utils import *
from .main import storage_service


@storage_service.post("/upload")
async def upload(
    file_name: UploadFile = File(),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print("Uploading file")
    # get the file name
    file: bytes = file_name.file.read()
    try:
        cid: str = produce_cid(file, file_name)
        if not cid:
            raise HTTPException(status_code=400, detail="Failed to produce CID")
        hash: str = generate_hash(cid)
        if not hash:
            raise HTTPException(status_code=400, detail="Failed to generate hash")
        user: User = current_user
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
    try:
        users_id = current_user.id
        data_record = assemble_record(
            file,
            file_name,
            cid,
            users_id,
        )

        db.add(data_record)
        db.commit()

    except sqlalchemy.exc.IntegrityError as e:
        return {"message": "File already exists", "file_hash": hash}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error") from e

    return {
        "cid": cid,
        "hash": hash,
        "user_id": current_user.username,
        "status": "success",
    }


# https://stribny.name/blog/fastapi-video/#:~:text=There%20is%20a%20simple%20mechanism,format%20bytes%3D1024000%2C2048000%20.
