import logging

from app.core.logging import setup_logging


def test_setup_logging_writes_rotating_file(tmp_path):
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level

    log_file = tmp_path / "backend.log"

    try:
        setup_logging(
            "INFO",
            log_to_file=True,
            log_file_path=str(log_file),
            log_file_max_bytes=1024,
            log_file_backup_count=2,
        )

        logger = logging.getLogger("tests.logging")
        logger.info("persist this line")

        for handler in root.handlers:
            if hasattr(handler, "flush"):
                handler.flush()

        assert log_file.exists()
        assert "persist this line" in log_file.read_text(encoding="utf-8")
    finally:
        new_handlers = [handler for handler in root.handlers if handler not in original_handlers]
        for handler in new_handlers:
            handler.close()

        root.handlers.clear()
        for handler in original_handlers:
            root.addHandler(handler)
        root.setLevel(original_level)
