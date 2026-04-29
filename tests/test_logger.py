# tests/test_logger.py
import os
import pytest
from logger import get_logger

def test_logger_writes_to_file(tmp_path):
    log_file = str(tmp_path / "test.log")
    logger = get_logger(log_file)
    logger.info("sender@test.com", "Test Subject", "פריקת מכולות", "replied")
    with open(log_file, encoding="utf-8") as f:
        line = f.readline()
    assert "sender@test.com" in line
    assert "replied" in line

def test_logger_writes_error(tmp_path):
    log_file = str(tmp_path / "test.log")
    logger = get_logger(log_file)
    logger.error("fetch failed: timeout")
    with open(log_file, encoding="utf-8") as f:
        line = f.readline()
    assert "ERROR" in line
    assert "fetch failed: timeout" in line
