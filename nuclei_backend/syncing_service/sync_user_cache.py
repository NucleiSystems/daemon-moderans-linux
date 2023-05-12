import asyncio
import base64
import pathlib
import pickle
import time
from functools import lru_cache
from os import environ
from pathlib import Path

import redis
from apscheduler.schedulers.background import BackgroundScheduler

from .scheduler_config import SchConfig


class RedisController:
    def __init__(self, user):
        self.user = user

    def __enter__(self):
        self.redis_connection = redis.Redis().from_url(
            url=environ.get("REDIS_URL"), decode_responses=True, db=0
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.redis_connection.close()

    def set_files(self, file: list[dict[str, bytes]]):
        with self:
            return self.redis_connection.set(str(self.user), str(file))

    def get_files(self):
        with self:
            return self.redis_connection.get(self.user)

    def clear_cache(self):
        with self:
            return self.redis_connection.delete(self.user)

    def check_files(self):
        with self:
            return self.redis_connection.exists(self.user)

    def set_file_count(self, count: int):
        with self:
            return self.redis_connection.set(f"{self.user}_count", count)

    def get_file_count(self):
        with self:
            count = self.redis_connection.get(f"{self.user}_count")
            return int(count) if count is not None else 0

    def delete_file_count(self):
        with self:
            return self.redis_connection.delete(f"{self.user}_count")


class FileCacheEntry:
    """A cache entry for a file in a directory."""

    def __init__(self, dir_id):
        """Create a new file cache entry for the specified directory."""
        self.dir_id = dir_id
        self.redis_connection = None

    def _connect_to_redis(self):
        """Connect to Redis."""
        if self.redis_connection is None:
            self.redis_connection = redis.Redis().from_url(
                url=environ.get("REDIS_URL"), decode_responses=True, db=1
            )

    def set_file_session_active(self) -> str:
        """Activate the file session for this cache entry."""
        self._connect_to_redis()
        self.redis_connection.set(f"file_session_cache_{self.dir_id}", "active")
        self.redis_connection.set(
            f"file_session_cache_activetime_{self.dir_id}", f"{time.ctime()}"
        )
        return "activated"

    def set_file_session_inactive(self) -> str:
        """Deactivate the file session for this cache entry."""
        self._connect_to_redis()
        self.redis_connection.set(f"file_session_cache_{self.dir_id}", "notactive")
        self.redis_connection.set(
            f"file_session_cache_deactivetime_{self.dir_id}", f"{time.ctime()}"
        )
        return "deactivated"

    def _delete_file(self, file_path):
        """Delete the file at the given path."""
        file_path.unlink()

    def check_and_delete_files(self):
        self._connect_to_redis()
        for key in self.redis_connection.scan_iter(match="file_session_cache_*"):
            status = self.redis_connection.get(key)
            if status == "notactive":
                dir_id = key.split("_")[3]
                deactivated_time = self.redis_connection.get(
                    f"file_session_cache_deactivetime_{dir_id}"
                )
                if (
                    time.time() - time.mktime(time.strptime(deactivated_time, "%c"))
                    >= 3600
                ):
                    file_path = (
                        pathlib.Path(__file__).parent / "FILE_PLAYING_FIELD" / dir_id
                    )
                    self._delete_file(file_path)

            elif status == "active":
                dir_id = key.split("_")[3]
                activated_time = self.redis_connection.get(
                    f"file_session_cache_activetime_{dir_id}"
                )
                if (
                    time.time() - time.mktime(time.strptime(activated_time, "%c"))
                    >= 3600
                ):
                    file_path = (
                        pathlib.Path(__file__).parent / "FILE_PLAYING_FIELD" / dir_id
                    )
                    self._delete_file(file_path)


class SchedulerController:
    def __init__(self):
        self.scheduler = BackgroundScheduler(
            executors=SchConfig.executors,
            job_defaults=SchConfig.job_defaults,
            timezone=SchConfig.timezone,
        )
        self.path = pathlib.Path(__file__).parent.absolute() / "FILE_PLAYING_FIELD"

    @lru_cache(maxsize=None)
    def start_scheduler(self):
        self.scheduler.start()

    def check_scheduler(self):
        return self.scheduler.running

    @lru_cache(maxsize=None)
    def add_job(self, job_id, func, trigger, **kwargs):
        self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            **kwargs,
        )
        self.scheduler.remove_job(job_id)


class FileListener(SchedulerController):
    def __init__(self, user_id, session_id):
        super().__init__()
        self.user_id = user_id
        self.redis = RedisController(user_id)
        self.session_id = session_id
        self.path = Path("path/to/files")

    async def file_listener(self):
        self.path / str(self.session_id)
        await asyncio.sleep(2)  # Use asyncio.sleep instead of time.sleep

        with open(f"{self.session_id}.internal.pickle", "rb") as f:
            data = pickle.load(f)

        dispatch_dict = {str(self.user_id): []}
        for file_path, file_size in data.items():
            with open(file_path, "rb") as f:
                while True:
                    if chunk := f.read(1024 * 1024):
                        dispatch_dict[str(self.user_id)].append(
                            {str(file_path): base64.b64encode(chunk).decode()}
                        )

                    else:
                        break
        dispatch_dict = str(dispatch_dict).replace("'", '"')
        self.redis.set_files(dispatch_dict)
