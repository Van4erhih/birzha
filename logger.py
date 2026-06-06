import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(log_level: str = "INFO", log_file: str = "app.log") -> None:
    """Configures the logging for the application."""
    log_directory = "logs"
    os.makedirs(log_directory, exist_ok=True)
    log_path = os.path.join(log_directory, log_file)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = RotatingFileHandler(
        log_path, maxBytes=10485760, backupCount=5 # 10 MB per file, 5 backup files
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Prevent duplicate logs from other libraries
    logger.propagate = False

    logging.getLogger("web3").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)


# Example usage (can be removed or modified later)
if __name__ == "__main__":
    setup_logging("DEBUG")
    logging.info("Logger configured successfully.")
    logging.debug("This is a debug message.")
    logging.warning("This is a warning message.")
    logging.error("This is an error message.")
