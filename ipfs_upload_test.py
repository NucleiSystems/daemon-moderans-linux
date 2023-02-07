import requests
import json
import os
import pathlib
from pathlib import Path

import requests
import json
from pathlib import Path

# request = requests.post("http://127.0.0.1:5001/api/v0/add", params={})

import requests

files = {
    "file": open("tree_file.txt", "rb"),
}

# response = requests.post(
#     "http://127.0.0.1:5002/api/v0/add?cid-version=1",
#     files=files,
# )

response = requests.post(
    "http://127.0.0.1:5002/api/v0/dht/get?key=123",
)

# response = requests.post("http://127.0.0.1:5002/api/v0/add?cid-version=1", files=files)

print(response.text)
