#!/usr/bin/env python
# -*- coding: utf-8 -*-
from synology_api import filestation, downloadstation, sys_info
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          CallbackQueryHandler, ConversationHandler)

import json
import logging
import telegram
import urllib.request
import ssl
import time

# Edit the credentials.py file first to use the bot
from credentials import (SYNOLOGY_NAS_BOT_TOKEN, SYNOLOGY_NAS_BOT_OWNER,
                         SYNOLOGY_NAS_BOT_IP, SYNOLOGY_NAS_BOT_PORT,
                         SYNOLOGY_NAS_BOT_ACCOUNT, SYNOLOGY_NAS_BOT_PASSWORD)

STRINGS = {
    'hello':
    'Hello! I am an automated Telegram bot written by @nicholaschum and @ivaniskandar to manage Synology NAS servers!',
    'torrent_link_found':
    'Torrent link added to the Download Station',
    'torrent_failed':
    'Failed to load torrent into Download Station',
    'error_not_owner':
    'You are not the Owner of this server - Access denied',
    'mirror_link_added':
    'Mirror link added to the Download Station',
    'magnet_prefix':
    'magnet:?xt=urn:btih:',
    'http_prefix':
    'http',
}

# Prevent SSL invocation complaints
ssl._create_default_https_context = ssl._create_unverified_context

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

# Instantiate all the logins for the server
fl = filestation.FileStation(SYNOLOGY_NAS_BOT_IP, SYNOLOGY_NAS_BOT_PORT,
                             SYNOLOGY_NAS_BOT_ACCOUNT,
                             SYNOLOGY_NAS_BOT_PASSWORD)
dwn = downloadstation.DownloadStation(
    SYNOLOGY_NAS_BOT_IP, SYNOLOGY_NAS_BOT_PORT, SYNOLOGY_NAS_BOT_ACCOUNT,
    SYNOLOGY_NAS_BOT_PASSWORD)
si = sys_info.SysInfo(SYNOLOGY_NAS_BOT_IP, SYNOLOGY_NAS_BOT_PORT,
                      SYNOLOGY_NAS_BOT_ACCOUNT, SYNOLOGY_NAS_BOT_PASSWORD)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    update.message.reply_text(STRINGS['hello'])


################################################################################
# Torrent Functions Listed Below
#
# The user can call /torrents and then an inline keyboard message will show up
#
# Torrent #0: [GutsySubs] Fly! Peek the Whale [DVD].mkv
# Status: downloading (27.93%)
#
# Torrent #1: [Miwako] Tamayomi #01 AT-X 1440x1080i HDTV.ts
# Status: downloading (3.17%)
#
# Torrent #2: [YES] Beyblade Burst Gachi - 01-52 END (AniTV 1920x1080 AVC AAC)
# Status: downloading (0.01%)
#
# You have 3 torrents in the queue.
################################################################################


def torrents(update, context):
    __enforceOwner(update)
    updateTorrentList(update)


def updateTorrentList(update):
    update.message.reply_text(
        torrentListData(),
        parse_mode=telegram.ParseMode.MARKDOWN_V2,
        reply_markup=torrentListReplyMarkup())


def updateTorrentListResponse(query):
    try:
        query.edit_message_text(
            torrentListData(),
            parse_mode=telegram.ParseMode.MARKDOWN_V2,
            reply_markup=torrentListReplyMarkup())
    except:
        print(
            "User tried to refresh the Torrent List, but it's the same message."
        )


def torrentListData():
    torrent_list = __cleanseShittyJsonOutput(str(dwn.tasks_list()))
    parsed = json.loads(torrent_list)
    reply_text = ""
    for x in range(parsed["data"]["total"]):
        current = parsed["data"]["tasks"][x]
        size = 0
        if current["size"] != 0:
            size = current["additional"]["transfer"][
                "size_downloaded"] / current["size"] * 100
        reply_text += "*Torrent #{0}:* `{1}`\n".format(x + 1, current["title"])
        reply_text += "*Status:* `{0} ({1}%)`\n\n".format(
            current["status"], str("{:.2f}".format(size)))
    reply_text += "You have *{0}* torrents in the queue.".format(
        parsed["data"]["total"])
    return __cleanseReply(reply_text)

def deleteCompletedTorrents():
    torrent_list = __cleanseShittyJsonOutput(str(dwn.tasks_list()))
    parsed = json.loads(torrent_list)
    reply_text = ""
    size = 0

    for x in range(parsed["data"]["total"]):
        current = parsed["data"]["tasks"][x]

        if current["additional"]["transfer"]["size_downloaded"] == current["size"]:
            reply_text += "Deleted {0}\n".format(current["title"])
            size += 1
            dwn.delete_task(current["id"])

    reply_text += "\nRemoved *{0}* torrents from the queue.".format(size)
    return __cleanseReply(reply_text)

def deleteAllTorrents():
    torrent_list = __cleanseShittyJsonOutput(str(dwn.tasks_list()))
    parsed = json.loads(torrent_list)
    reply_text = ""
    size = 0

    for x in range(parsed["data"]["total"]):
        current = parsed["data"]["tasks"][x]
        reply_text += "Deleted {0}\n".format(current["title"])
        dwn.delete_task(current["id"])
        size += 1

    reply_text += "\nRemoved *{0}* torrents from the queue.".format(size)
    return __cleanseReply(reply_text)

def getDownloadStationDownloadLocation():
    download_station = __cleanseShittyJsonOutput(str(dwn.get_config()))
    return download_station["data"]["default_destination"]

def torrentListReplyMarkup():
    keyboard = [[
        InlineKeyboardButton("Pause Torrents", callback_data='1'),
        InlineKeyboardButton("Resume Torrents", callback_data='2')
    ], [
        InlineKeyboardButton("Refresh List", callback_data='3'),
        InlineKeyboardButton("Delete Completed", callback_data='4')],
        [InlineKeyboardButton("Delete All Torrents", callback_data='5')]]
    return InlineKeyboardMarkup(keyboard)

def torrentListButtons(update, context):
    query = update.callback_query
    query.answer()
    if (query.data == "1"):
        query.edit_message_text(text="Pausing all torrents...")
        torrent_list = __cleanseShittyJsonOutput(str(dwn.tasks_list()))
        parsed = json.loads(torrent_list)
        for x in range(parsed["data"]["total"]):
            current = parsed["data"]["tasks"][x]
            dwn.pause_task(current["id"])
    elif (query.data == "2"):
        query.edit_message_text(text="Resuming all torrents...")
        torrent_list = __cleanseShittyJsonOutput(str(dwn.tasks_list()))
        parsed = json.loads(torrent_list)
        for x in range(parsed["data"]["total"]):
            current = parsed["data"]["tasks"][x]
            dwn.resume_task(current["id"])
    elif (query.data == "4"):
        query.edit_message_text(text="Deleting completed torrents...")
        time.sleep(1)
        query.edit_message_text(text=deleteCompletedTorrents(), parse_mode=telegram.ParseMode.MARKDOWN_V2)
        time.sleep(1)
    elif (query.data == "5"):
        query.edit_message_text(text="Deleting all torrents...")
        time.sleep(1)
        query.edit_message_text(text=deleteAllTorrents(), parse_mode=telegram.ParseMode.MARKDOWN_V2)
        time.sleep(1)
    updateTorrentListResponse(query)


def networkStatus(update, context):
    __enforceOwner(update)
    networkStatus = __cleanseShittyJsonOutput(str(si.network_status()))
    vpnStatus = __cleanseShittyJsonOutput(str(
        si.network_vpn_pptp()))  # we can add the openVPN checks
    parsed = json.loads(networkStatus)
    parsed2 = json.loads(vpnStatus)

    reply_text = ""
    server_name = parsed["data"]["server_name"]
    dns_primary = parsed["data"]["dns_primary"]
    dns_secondary = parsed["data"]["dns_secondary"]
    ip = parsed["data"]["gateway_info"]["ip"]
    vpn = parsed2["data"]

    reply_text = "Server Name: {0}".format(server_name)
    # DNS Primary is a must, or else there's no Telegram Bot
    reply_text += "\nDNS Primary: {0}".format(dns_primary)
    if len(dns_secondary) > 0:
        reply_text += "\nDNS Secondary: {0}".format(dns_secondary)
    # We should be able to get at least one ip
    reply_text += "\nIP Address: {0}".format(ip)
    if len(vpn) > 0:
        reply_text += "\nVPN: Yes"
    else:
        reply_text += "\nVPN: No"

    update.message.reply_text(
        __cleanseReply(reply_text), parse_mode=telegram.ParseMode.MARKDOWN_V2)


def processText(update, context):
    __enforceOwner(update)
    message = update.message.text
    if message.startswith(STRINGS["http_prefix"]):
        try:
            dwn.task_create(message)
            update.message.reply_text("{0}".format(STRINGS["torrent_link_found"]))
        except:
            update.message.reply_text("{0}".format(STRINGS["torrent_failed"]))
    elif message.startswith(STRINGS["magnet_prefix"]):
        try:
            dwn.task_create(message)
            update.message.reply_text("{0}".format(STRINGS["mirror_link_added"]))
        except:
            update.message.reply_text("{0}".format(STRINGS["torrent_failed"]))



def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# Common Functions


def __cleanseShittyJsonOutput(input):
    return input.replace("'", "\"").replace("True", "true").replace(
        "False", "false")


def __cleanseReply(input):
    return input.replace("-", "\\-").replace("_", "\_").replace(
        ".", "\.").replace("(",
                           "\(").replace(")", "\)").replace("[", "\[").replace(
                               "]", "\]").replace("#", "\#").replace(
                                   "{", "\{").replace("}", "\}")


def __enforceOwner(update):
    # only accept messages from the owner
    if str(update.message.chat_id) != SYNOLOGY_NAS_BOT_OWNER:
        update.message.reply_text(STRINGS['error_not_owner'])
        return


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(SYNOLOGY_NAS_BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("torrents", torrents))

    dp.add_handler(CallbackQueryHandler(torrentListButtons))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, processText))
    dp.add_handler(MessageHandler(Filters.document.mime_type('application/x-bittorrent'), start))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
