import logging

def get_logger(log_file: str = "automation.log") -> "AutoLogger":
    return AutoLogger(log_file)

class AutoLogger:
    def __init__(self, log_file: str):
        self._logger = logging.getLogger(log_file)
        self._logger.setLevel(logging.DEBUG)
        if not self._logger.handlers:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self._logger.addHandler(fh)

    def info(self, sender: str, subject: str, keyword: str, action: str):
        self._logger.info(f"sender={sender} subject={subject!r} keyword={keyword!r} action={action}")

    def warning(self, msg: str):
        self._logger.warning(f"WARNING {msg}")

    def error(self, msg: str):
        self._logger.error(f"ERROR {msg}")
