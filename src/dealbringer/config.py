import os
from pathlib import Path


def data_directory() -> Path:
    return Path(os.environ.get("DEALBRINGER_DATA_DIR", "./data")).expanduser()
