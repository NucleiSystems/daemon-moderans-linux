import contextlib
from functools import total_ordering, lru_cache
import logging
import shutil
import subprocess
import time

from fastapi import Depends, HTTPException
import os, pathlib

from ..storage_service.ipfs_model import DataStorage
from ..users.auth_utils import get_current_user
from ..users.user_handler_utils import get_db
from ..users.user_models import User
from .sync_user_cache import FileListener, RedisController, SchedulerController
from uuid import uuid4
from pathlib import Path
import json
import contextlib


def get_user_cids(user_id, db) -> list:
    try:
        query = db.query(DataStorage).filter(DataStorage.owner_id == user_id).all()
        return query
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


def get_collective_bytes(user_id, db):
    try:
        query = db.query(DataStorage).filter(DataStorage.owner_id == user_id).all()
        return sum(x.file_size for x in query)
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


class UserDataExtraction:
    def __init__(self, user_id, db, cids: list):
        self.user_id = user_id
        self.session_id = uuid4()

        self.db = db
        self.user_data = get_user_cids(self.user_id, self.db)
        self.file_bytes = []
        self.cids = cids
        self.ipget_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "utils/ipget")
        )
        self.new_folder = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), f"FILE_PLAYING_FIELD/{self.session_id}"
            )
        )

    def download_file_ipfs(self):
        with contextlib.suppress(PermissionError):
            os.mkdir(self.new_folder)
            os.chdir(self.new_folder)

            for _ in self.cids:
                while True:
                    print("inside of the while loop")
                    try:
                        file = f"{self.ipget_path} --node=local {_.file_cid} -o {_.file_name} --progress=true"
                        subprocess.Popen(str(f"{file}"), shell=True)
                        print(
                            f"Started downloading {_.file_name} ({_.file_cid}) - Session ID: {self.session_id}"
                        )
                        time.sleep(5)
                        if os.path.isfile(_.file_name):
                            print(f"Successfully downloaded {_.file_name}")
                            break
                    except Exception as e:
                        print(f"Error while downloading {_.file_name}: {e}")
                        raise e

            self.write_file_summary()

            while not self.insurance():
                print(
                    "Some files are still being downloaded, waiting for completion..."
                )
                time.sleep(5)

        print("All files downloaded successfully!")

    def write_file_summary(self):
        with contextlib.suppress(PermissionError):
            file_sum = {
                _.file_name: {
                    "file_name": _.file_name,
                    "file_cid": _.file_cid,
                    "file_size": _.file_size,
                }
                for _ in self.cids
            }
            with open(f"{self.session_id}.internal.json", "w") as f:
                json.dump(file_sum, f)

    def insurance(self) -> bool:
        for _ in self.cids:
            if not os.path.isfile(f"{_.file_name}"):
                return False
            _bytes = open(_.file_name, "rb")
            if len(_bytes.read()) != _.file_size:
                return False
            del _bytes
        return True

    async def cleanup(self):
        with contextlib.suppress(PermissionError):
            os.chdir(pathlib.Path(self.new_folder).parent)

            await shutil.rmtree(
                pathlib.Path(self.new_folder),
                ignore_errors=False,
            )
