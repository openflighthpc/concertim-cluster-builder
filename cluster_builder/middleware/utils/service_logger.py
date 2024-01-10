# Py Packages
import logging
import os

def create_logger(name, log_file, level):
    logger = logging.getLogger(name)
    if logger.hasHandlers(): 
        logger.handlers.clear()
    levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}
    lvl = (levels[level.upper()])
    logger.setLevel(lvl)
    formatter = SensitiveFormatter('[%(asctime)s] - %(levelname)-8s: %(module)-12s: %(funcName)-26s===>  %(message)s')
    dir_name = os.path.dirname(log_file)
    try:
        # Create directories if they don't exist
        os.makedirs(dir_name, exist_ok=True)

        # Create the log file if it doesn't exist
        if not os.path.exists(log_file):
            open(log_file, 'w').close()
    except Exception as e:
        raise Exception(f"Could not create log file: {log_file} - {type(e).__name__} - {e}")

    try:
        # File handler for log file with given log level from CONFIG
        fh = logging.FileHandler(log_file)
        fh.setLevel(lvl)
        fh.setFormatter(formatter)
        # Console handler for console output with WARNING log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)
    except Exception as e:
        raise Exception(f"Could not create FileHandler for log file: {log_file} - {type(e).__name__} - {e}")
    
    return logger


class SensitiveFormatter(logging.Formatter):

    def format(self, record):
        original = logging.Formatter.format(self, record)
        if 'password' in original:
            filtered = original.split("===>")[0] + "===>  << Message contains a 'password' string - REDACTING >>"
            return filtered
        return original