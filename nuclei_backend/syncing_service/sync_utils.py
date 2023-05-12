import asyncio
import concurrent.futures
import contextlib
import json
import logging
import os
import pathlib
import shutil
import subprocess
import time
from typing import List
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..storage_service.ipfs_model import DataStorage


def get_user_cids(user_id: int, db: Session) -> List[DataStorage]:
    try:
        return db.query(DataStorage).filter(DataStorage.owner_id == user_id).all()
    except Exception as e:
        logging.exception(e)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve user's data"
        ) from e


def get_collective_bytes(user_id: int, db) -> int:
    try:
        query = db.query(DataStorage).filter(DataStorage.owner_id == user_id).all()
        return sum(x.file_size for x in query)
    except Exception as e:
        logging.exception("Error getting collective bytes")
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


class UserDataExtraction:
    def __init__(self, user_id: str, db: Session, cids: List[str]):
        self.user_id = user_id
        self.session_id = str(uuid4())
        self.db = db
        self.cids = cids
        self.user_data = []

        self.new_folder = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), f"FILE_PLAYING_FIELD/{self.session_id}"
            )
        )
        self.ipfs_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "utils/ipfs")
        )

    def run(self):
        self.user_data = self.get_user_cids()
        self.download_file_ipfs()
        self.write_file_summary()
        self.insurance()
        self.cleanup()

    def get_user_cids(self):
        return (
            self.db.query(DataStorage)
            .filter(DataStorage.owner_id == self.user_id)
            .all()
        )

    def download_file_ipfs(self):
        os.mkdir(self.new_folder)
        os.chdir(self.new_folder)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            tasks = []
            for cid in self.cids:
                task = loop.run_in_executor(executor, self.download_file, cid)
                tasks.append(task)
            loop.run_until_complete(asyncio.gather(*tasks))

        while not self.insurance():
            time.sleep(5)

    def download_file(self, cid):
        while True:
            try:
                subprocess.check_call(
                    [
                        f"{self.ipfs_path}",
                        "get",
                        cid,
                        "-o",
                        self.get_file_name(cid),
                        "--progress=true",
                    ]
                )

                time.sleep(5)
                if os.path.isfile(self.get_file_name(cid)):
                    break
            except Exception as e:
                raise e

    def get_file_name(self, cid):
        for data in self.user_data:
            if data.file_cid == cid:
                return data.file_name

    def write_file_summary(self):
        with contextlib.suppress(PermissionError):
            file_sum = {
                data.file_name: {
                    "file_name": data.file_name,
                    "file_cid": data.file_cid,
                    "file_size": data.file_size,
                }
                for data in self.user_data
            }
            with open(f"{self.session_id}.internal.json", "w") as f:
                json.dump(file_sum, f)

    def insurance(self) -> bool:
        for data in self.user_data:
            if not os.path.isfile(self.get_file_name(data.file_cid)):
                return False
            _bytes = open(self.get_file_name(data.file_cid), "rb")
            if len(_bytes.read()) != data.file_size:
                return False
            del _bytes
        return True

    def cleanup(self):
        with contextlib.suppress(PermissionError):
            os.chdir(pathlib.Path(self.new_folder).parent)

            shutil.rmtree(
                pathlib.Path(self.new_folder),
                ignore_errors=False,
            )
