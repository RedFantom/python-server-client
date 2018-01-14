"""
Author: RedFantom
License: GNU GPLv3
Copyright (C) 2018 RedFantom

Docstrings wrapped to 72 characters, line-comments to 80 characters,
code to 120 characters.
"""
import logging


def setup_logger(name, file, std_level=logging.ERROR, file_level=logging.DEBUG):
    """
    Setup a logger instance and assign it to the class attribute
    to allow logging to stdout and file with info and debug messages
    :param name: Logger name
    :param file: Logger file name
    :param std_level: Logging level for stdout
    :param file_level: Logging level for log file
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(file)
    fh.setLevel(file_level)
    ch = logging.StreamHandler()
    ch.setLevel(std_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
