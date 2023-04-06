import logging
import pathlib
from typing import List
from uuid import uuid4
import os
import io
from PIL import Image
import psutil
import zstandard as zstd
import PIL.Image
from fastapi import UploadFile
from concurrent.futures import ThreadPoolExecutor

from ..CompressionBase import CompressionImpl
from ..ipfs_utils import *

logger = logging.getLogger(__name__)


class CompressImage(CompressionImpl):
    def __init__(self, file: bytes, filename: str):
        super().__init__(app_path="image")

        self.file = file
        self.filename = filename
        self.compression_temp_file = self.save_to_temp(self.file, self.filename)

    def cleanup_compression_outcome(self):
        pathlib.Path(self.compression_temp_file[0]).unlink()

    def produce_compression(self) -> bytes:
        print("compressing image")
        with open(self.compression_temp_file[0], "rb") as f:
            original_data = f.read()
        file_size = len(original_data)
        avg_image_size = 5000000  # example average size of an image in bytes
        if (
            file_size < avg_image_size * 0.8
        ):  # use first function for files smaller than 1MB
            compression_level = lambda data: min(22, max(1, round(len(data) / 100000)))
        else:  # use second function for files larger than 1MB
            compression_level = lambda file_size: min(
                22,
                max(
                    1,
                    round(
                        18
                        - (18 * file_size) / (0.8 * psutil.virtual_memory().available)
                    ),
                ),
            )
        compressor = zstd.ZstdCompressor(level=compression_level(original_data))
        compressed_data = compressor.compress(original_data)
        print("image compressed")
        return compressed_data


class ImageCompressionTask:
    def __init__(
        self, file: bytes, filename: str, identity_token: str, ipfs_flag: bool, db
    ):
        self.file = file
        self.filename = filename
        self.identity_token = identity_token
        self.ipfs_flag = ipfs_flag
        self.db = db

    def __call__(self):
        try:
            compressing_file = CompressImage(self.file, self.filename)

            compressed_file = compressing_file.produce_compression()
            if self.ipfs_flag:
                compressing_file.commit_to_ipfs(
                    compressed_file, self.filename, self.identity_token, self.db
                )
            compressing_file.cleanup_compression_outcome()
        except Exception as e:
            logger.error(
                f"Error compressing and storing file {self.filename}: {str(e)}"
            )


class ImageCompressionQueue:
    def __init__(self, num_threads: int):
        self.queue = []
        self.num_threads = num_threads

    def add_task(self, task: ImageCompressionTask):
        self.queue.append(task)

    def start(self):
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            for task in self.queue:
                executor.submit(task)


class ImageCompression:
    def __init__(self, ipfs_flag: bool, identity_token: str, db):
        self.ipfs_flag = ipfs_flag
        self.identity_token = identity_token
        self.db = db

    def process_files(self, files: List[UploadFile]):
        queue = ImageCompressionQueue(num_threads=4)  # can adjust the number of threads
        for file in files:
            _file = file.file.read()
            filename = file.filename
            queue.add_task(
                ImageCompressionTask(
                    _file, filename, self.identity_token, self.ipfs_flag, self.db
                )
            )
        queue.start()
