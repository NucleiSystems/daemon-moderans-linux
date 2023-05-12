import asyncio
import concurrent.futures
import contextlib
import json

from fastapi import Depends

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

executor = concurrent.futures.ThreadPoolExecutor()


class RequestHandler:
    def __init__(self, max_queue_size=10):
        self.queue = []
        self.max_queue_size = max_queue_size

    async def handle_request(self, user_id, db):
        self.queue.append((user_id, db))
        if len(self.queue) > self.max_queue_size:
            await self.process_requests()
        else:
            await self.async_fetch_files(user_id, db)

    async def async_fetch_files(self, user_id, db):
        with contextlib.suppress(PermissionError):
            cids = get_user_cids(user_id, db)
            queried_bytes = get_collective_bytes(user_id, db)
            files = UserDataExtraction(user_id, db, cids)
            file_session_cache = FileCacheEntry(files.session_id)
            redis_controller = RedisController(user=str(user_id))
            if redis_controller.check_files():
                cached_file_count = redis_controller.get_file_count()
                if cached_file_count == len(cids):
                    return {
                        "message": "Files are already in cache",
                        "cids": cids,
                        "bytes": queried_bytes,
                    }
                else:
                    redis_controller.delete_file_count()
            files.download_file_ipfs()
            files.write_file_summary()
            if files.insurance():
                file_session_cache.activate_file_session()
            file_listener = FileListener(user_id, files.session_id)
            file_listener.file_listener()
            scheduler_controller = SchedulerController()
            if scheduler_controller.check_scheduler():
                scheduler_controller.start_scheduler()
            await asyncio.sleep(10)
            redis_controller.set_file_count(len(cids))
            try:
                files.cleanup()
            except Exception as e:
                print(e)
            file_session_cache.activate_file_session()

        return {
            "message": "Dispatched",
            "cids": cids,
            "bytes": queried_bytes,
        }

    async def process_requests(self):
        requests_to_process = self.queue
        self.queue = []
        sorted_requests = self.sort_requests(requests_to_process)
        for user_id, db in sorted_requests:
            await self.async_fetch_files(user_id, db)

    def get_files_count_for_user(self, user_id, db) -> int:
        return db.query(DataStorage).filter(DataStorage.user_id == user_id).count()

    def sort_requests(self, requests) -> list:
        # Get the number of files each user has uploaded from the database
        users_files_count = {}
        for user_id, db in requests:
            files_count = self.get_files_count_for_user(
                user_id, db
            )  # Query the database for the number of files
            users_files_count[user_id] = files_count

        requests.sort(key=lambda r: users_files_count[r[0]])
        return requests


request_handler = RequestHandler()


@sync_router.get("/fetch/all")
async def dispatch_all(user: User = Depends(get_current_user), db=Depends(get_db)):
    try:
        await request_handler.handle_request(user.id, db)
        return {"message": "Dispatched"}
    except Exception:
        raise


@sync_router.get("/fetch/redis/all")
async def redis_cache_all(user: User = Depends(get_current_user)):
    try:
        all_files = RedisController(str(user.id)).get_files()
        # extract the json from all_files
        all_files = json.loads(all_files)

        return {
            "files": all_files,
            "user_id": user.id,
        }
    except Exception as e:
        print(e)


@sync_router.post("/fetch/delete/all")
def delete_all(user: User = Depends(get_current_user), db=Depends(get_db)):
    db.query(DataStorage).delete()
    db.commit()
    return {"message": "deleted"}


@sync_router.get("/fetch/redis/clear")
async def redis_cache_clear(user: User = Depends(get_current_user)):
    return RedisController(str(user.id)).clear_cache()


@sync_router.get("/all")
def return_all(user: User = Depends(get_current_user), db=Depends(get_db)):
    user_data = (
        db.query(User).filter(User.id == user.id).all(),
        db.query(DataStorage).filter(DataStorage.owner_id == user.id).all(),
    )

    return {
        "user": user_data,
    }
