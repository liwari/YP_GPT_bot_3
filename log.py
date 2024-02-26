import logging

log_file_name = "log_file.txt"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=log_file_name,
    filemode="a",
    encoding="utf8"
)


def log_info(text: str):
    logging.info(text)


def log_error(text: str):
    logging.error(text)


def get_log_file():
    return open(log_file_name, "rb")
