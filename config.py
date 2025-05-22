import logging
from logging import getLogger

logger = getLogger('Novel Downloader')
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()

formatter = logging.Formatter("%(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)
