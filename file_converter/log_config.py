import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "converter.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"


def daily_file_handler(path: Path, level: int) -> TimedRotatingFileHandler:
    handler = TimedRotatingFileHandler(path, when="midnight", backupCount=10, encoding="utf-8")
    handler.setLevel(level)
    return handler


def configure_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            daily_file_handler(LOG_FILE, logging.INFO),
            daily_file_handler(ERROR_LOG_FILE, logging.ERROR),
        ],
    )
