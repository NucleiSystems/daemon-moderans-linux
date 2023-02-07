import contextlib
import json
import os
import pathlib
import random
import time
import uuid
from functools import lru_cache, total_ordering

from fastapi import Depends
from fastapi_utils.tasks import repeat_every

from ..storage_service.ipfs_model import DataStorage
from ..users.auth_utils import get_current_user
from ..users.user_handler_utils import get_db
from ..users.user_models import User
from .sync_service_main import sync_router
from .sync_user_cache import (
    FileCacheEntry,
    FileListener,
    RedisController,
    SchedulerController,
)
from .sync_utils import UserDataExtraction, get_collective_bytes, get_user_cids


@sync_router.get("/fetch/all")
async def dispatch_all(user: User = Depends(get_current_user), db=Depends(get_db)):
    with contextlib.suppress(PermissionError):
        cids = get_user_cids(user.id, db)
        queried_bytes = get_collective_bytes(user.id, db)
        files = UserDataExtraction(user.id, db, cids)
        file_session_cache = FileCacheEntry(files.session_id)

        redis_controller = RedisController(user=str(user.id))

        if redis_controller.check_files():
            cached_file_count = redis_controller.get_file_count()
            if cached_file_count == len(cids):
                return {
                    "message": "Files are already in cache",
                    "cids": cids,
                    "bytes": queried_bytes,
                }
            else:
                await redis_controller.delete_file_count()

        try:
            files.download_file_ipfs()
            file_session_cache.activate_file_session()
            file_listener = FileListener(user.id, files.session_id)

            file_listener.file_listener()

            scheduler_controller = SchedulerController()
            if scheduler_controller.check_scheduler():
                scheduler_controller.start_scheduler()

            time.sleep(10)

        except Exception as e:
            raise e

        redis_controller.set_file_count(len(cids))

        try:
            await files.cleanup()
        except Exception as e:
            print(e)
        file_session_cache.activate_file_session()

    return {
        "message": "Dispatched",
        "cids": cids,
        "bytes": queried_bytes,
    }


@sync_router.on_event("startup")
@repeat_every(seconds=60 * 60)
def remove_false_folders():
    try:
        FileCacheEntry.check_and_delete_files()
    except Exception as e:
        raise e


@sync_router.get("/fetch/redis/all")
async def redis_cache_all(user: User = Depends(get_current_user)):
    # get all redis cache pertaining to the user
    all_files = RedisController(str(user.id)).get_files()
    # extract the json from all_files
    all_files = json.loads(all_files)

    return {
        "files": all_files,
    }


@sync_router.get("/file/cache/all")
async def file_cache_all(user: User = Depends(get_current_user)):
    # delete all files
    ...


@sync_router.post("/fetch/delete/all")
def delete_all(user: User = Depends(get_current_user), db=Depends(get_db)):
    db.query(DataStorage).delete()
    db.commit()
    return {"message": "deleted"}


@sync_router.get("/fetch/redis/clear")
async def redis_cache_clear(user: User = Depends(get_current_user)):
    return RedisController(str(user.id)).clear_cache()


@sync_router.get("/fetch/redis/test")
async def redis_cache_test(user: User = Depends(get_current_user), db=Depends(get_db)):
    user_id = "user_1"
    session_id = "session_1"
    # redis test
    redis = RedisController(user_id)
    redis.initialise_user()
    redis.set_upload_user_files(["file_1", "file_2", "file_3"])
    return {redis.serialize_user_files()}


@sync_router.get("/all")
def return_all(user: User = Depends(get_current_user), db=Depends(get_db)):
    user_data = (
        db.query(User).filter(User.id == user.id).all(),
        db.query(DataStorage).filter(DataStorage.owner_id == user.id).all(),
    )

    return {
        "user": user_data,
    }
