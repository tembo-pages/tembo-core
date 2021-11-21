"""Subpackage that contains the CLI application."""

import os
from typing import Any

import panaetius
from panaetius.exceptions import LoggingDirectoryDoesNotExistException

if (config_path := os.environ.get("TEMBO_CONFIG")) is not None:
    CONFIG: Any = panaetius.Config("tembo", config_path, skip_header_init=True)
else:
    CONFIG = panaetius.Config("tembo", "~/tembo/.config", skip_header_init=True)


panaetius.set_config(CONFIG, "base_path", "~/tembo")
panaetius.set_config(CONFIG, "template_path", "~/tembo/.templates")
panaetius.set_config(CONFIG, "scopes", {})
panaetius.set_config(CONFIG, "logging.level", "DEBUG")
panaetius.set_config(CONFIG, "logging.path")

try:
    logger = panaetius.set_logger(
        CONFIG, panaetius.SimpleLogger(logging_level=CONFIG.logging_level)
    )
except LoggingDirectoryDoesNotExistException:
    _LOGGING_PATH = CONFIG.logging_path
    CONFIG.logging_path = ""
    logger = panaetius.set_logger(
        CONFIG, panaetius.SimpleLogger(logging_level=CONFIG.logging_level)
    )
    logger.warning("Logging directory %s does not exist", _LOGGING_PATH)
