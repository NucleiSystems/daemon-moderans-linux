import os

from nuclei_backend.permanent_store.chunking import Chunker


class NormaliseFile:
    def __init__(self, file):
        self.file = file

    def run(self):
        self.produce_chunks()

    def produce_chunks(self):
        chunker = Chunker(self.file.filename)
        try:
            chunker.generic_run()
        except Exception as e:
            print(e)


class FileDigestion:
    def __init__(self, file):
        self.file = file

    def digest(self):
        with open(self.file.filename, "wb+") as f:
            f.write(self.file.file.read())

    def remove(self):
        os.remove(self.file.filename)
