import importlib
import logging
import os
import ssl
import sys

from telegram.ext import Updater

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)

LOGGER = logging.getLogger(__name__)

# Prevent SSL invocation complaints
ssl._create_default_https_context = ssl._create_unverified_context

try:
    from .credentials import (SYNOLOGY_NAS_BOT_TOKEN, SYNOLOGY_NAS_BOT_OWNER,
                             SYNOLOGY_NAS_BOT_IP, SYNOLOGY_NAS_BOT_PORT,
                             SYNOLOGY_NAS_BOT_ACCOUNT, SYNOLOGY_NAS_BOT_PASSWORD)
    LOGGER.info("Importing credentials from file")
    BOT_TOKEN = SYNOLOGY_NAS_BOT_TOKEN
    BOT_OWNER_ID = SYNOLOGY_NAS_BOT_OWNER
    NAS_IP = SYNOLOGY_NAS_BOT_IP
    NAS_PORT = SYNOLOGY_NAS_BOT_PORT
    DSM_ACCOUNT = SYNOLOGY_NAS_BOT_ACCOUNT
    DSM_PASSWORD = SYNOLOGY_NAS_BOT_PASSWORD
except ModuleNotFoundError:
    LOGGER.info("Importing credentials from env")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    BOT_OWNER_ID = os.environ.get("BOT_OWNER_ID")
    NAS_IP = os.environ.get("NAS_IP")
    NAS_PORT = os.environ.get("NAS_PORT")
    DSM_ACCOUNT = os.environ.get("DSM_ACCOUNT")
    DSM_PASSWORD = os.environ.get("DSM_PASSWORD")

LOGGER.info("Starting bot for {0}@{1}:{2}".format(DSM_ACCOUNT, NAS_IP, NAS_PORT))

updater = Updater(BOT_TOKEN, use_context=True)

dispatcher = updater.dispatcher

START_MESSAGE = """Hi! I can hear (or read?) you clearly and I'm ready to do my job.

You can control me by sending these commands:

"""

# Needed values are set, time load load the modules
from syno_bot.modules import ALL_MODULES
for module_name in ALL_MODULES:
    imported_module = importlib.import_module("syno_bot.modules." + module_name)
    if hasattr(imported_module, "__help__") and imported_module.__help__:
        START_MESSAGE += imported_module.__help__
