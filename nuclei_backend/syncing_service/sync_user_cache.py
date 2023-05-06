import json
import shutil
import redis
import time
import pathlib
from apscheduler.schedulers.background import BackgroundScheduler
from functools import lru_cache
from .scheduler_config import SchConfig
from os import environ
import base64


class RedisController:
    def __init__(self, user):
        self.redis_connection = redis.Redis().from_url(
            url=environ.get("REDIS_URL"), decode_responses=True, db=0
        )
        self.user = user

    def set_files(self, file: list[dict[str, bytes]]):
        return self.redis_connection.set(str(self.user), str(file))

    def get_files(self):
        # get the list of files for a user
        return self.redis_connection.get(self.user)

    def clear_cache(self):
        return self.redis_connection.delete(self.user)

    def check_files(self):
        return self.redis_connection.exists(self.user)

    def set_file_count(self, count: int):
        return self.redis_connection.set(f"{self.user}_count", count)

    def get_file_count(self):
        return (
            int(self.redis_connection.get(f"{self.user}_count"))
            if self.redis_connection.exists(f"{self.user}_count")
            else 0
        )

    async def delete_file_count(self):
        await self.redis_connection.delete(f"{self.user}_count")


class FileCacheEntry:
    """A cache entry for a file in a directory."""

    def __init__(self, dir_id):
        """Create a new file cache entry for the specified directory."""
        self.dir_id = dir_id
        self.redis_connection = redis.Redis().from_url(
            url=environ.get("REDIS_URL"), decode_responses=True, db=1
        )

    def activate_file_session(self):
        """Activate the file session for this cache entry."""
        self.redis_connection.set(f"file_session_cache&{str(self.dir_id)}", "active")
        self.redis_connection.set(
            f"file_session_cache_activetime&{str(self.dir_id)}", f"{time.ctime()}"
        )
        return "activated"

    def deactivate_file_session(self):
        """Deactivate the file session for this cache entry."""
        self.redis_connection.set(
            f"file_session_cache_id&{str(self.dir_id)}", "notactive"
        )
        self.redis_connection.set(
            f"file_session_cache_deactivetime&{str(self.dir_id)}", f"{time.ctime()}"
        )
        return "deactivated"

    def _deactivate_file_session(
        self, cache_id_key, status_value, cache_time_key, time_value
    ):
        """Helper method to deactivate a file session."""
        self.redis_connection.set(f"{cache_id_key}{str(self.dir_id)}", status_value)
        self.redis_connection.set(f"{cache_time_key}{str(self.dir_id)}", time_value)
        return "deactivated"

    @classmethod
    def check_and_delete_files(cls):
        """Check for and delete files that have been inactive for more than an hour."""
        for key in cls.redis_connection.scan_iter(match="file_session_cache_id&*"):
            status = cls.redis_connection.get(key)
            if status == b"notactive":
                dir_id = key.split("&")[1]
                deactivated_time = cls.redis_connection.get(
                    f"file_session_cache_deactivetime&{dir_id}"
                )
                if (
                    time.time() - time.mktime(time.strptime(deactivated_time, "%c"))
                    >= 3600
                ):
                    pathlib.Path.unlink(
                        __file__
                    ).parent.absolute() / "FILE_PLAYING_FIELD" / f"{dir_id}"
            elif status == b"active":
                dir_id = key.split("&")[1]
                activated_time = cls.redis_connection.get(
                    f"file_session_cache_activetime&{dir_id}"
                )
                if (
                    time.time() - time.mktime(time.strptime(activated_time, "%c"))
                    >= 3600
                ):
                    pathlib.Path.unlink(
                        __file__
                    ).parent.absolute() / "FILE_PLAYING_FIELD" / f"{dir_id}"


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

    def file_listener(self):
        folder_path = self.path / str(self.session_id)
        print("folder path", folder_path)
        time.sleep(2)
        files_index = open(f"{self.session_id}.internal.json", "r").read()
        data = json.loads(files_index)
        data = dict(data)
        data = data.items()
        dispatch_dict = {str(self.user_id): []}

        for _ in data:
            with open(_[0], "rb") as file_read_buffer:
                file_read_buffer = file_read_buffer.read()

            dispatch_dict[str(self.user_id)].append(
                {str(_[0]): base64.encodebytes(file_read_buffer).decode()}
            )
        dispatch_dict = str(dispatch_dict).replace("'", '"')
        print(f"dispatch_dict: {dispatch_dict}")
        self.redis.set_files(dispatch_dict)
        time.wait(10)
