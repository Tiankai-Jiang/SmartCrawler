import logging

def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():  # Avoid adding handlers multiple times
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s')

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler('crawler.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger