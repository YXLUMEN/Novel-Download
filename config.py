import logging
from logging import getLogger
from typing import Any

logger = getLogger('Novel Downloader')
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s -%(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

CONFIG: dict[str, Any] = {
    'default_download_path': './download'
}
