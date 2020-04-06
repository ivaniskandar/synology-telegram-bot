# -*- coding: utf-8 -*-
import time

from synology_api.sys_info import SysInfo, DSM, Storage
from syno_bot import dispatcher, NAS_IP, NAS_PORT, DSM_ACCOUNT, DSM_PASSWORD
from syno_bot.modules import ACTION_EDIT, ACTION_REPLY
from syno_bot.modules.helper.bot_decorator import send_typing_action
from syno_bot.modules.helper.conversation import cancel_other_conversations
from syno_bot.modules.helper.file_size import human_readable_size
from syno_bot.modules.helper.user_status import user_owner
from syno_bot.modules.helper.string_processor import escape_reserved_character
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler

sys_info = SysInfo.login(DSM_ACCOUNT, DSM_PASSWORD, NAS_IP, NAS_PORT)
dsm = DSM.login(DSM_ACCOUNT, DSM_PASSWORD, NAS_IP, NAS_PORT)
strg = Storage.login(DSM_ACCOUNT, DSM_PASSWORD, NAS_IP, NAS_PORT)

RELOADABLE_STATE = 1

@user_owner
@send_typing_action
def __nas_network_status(update, context):
    cancel_other_conversations(update, context)
    __show_nas_network_status(update.message)
    return RELOADABLE_STATE


@user_owner
@send_typing_action
def __resource_monitor(update, context):
    cancel_other_conversations(update, context)
    __show_resource_monitor(update.message)
    return RELOADABLE_STATE


@user_owner
@send_typing_action
def __nas_health_status(update, context):
    cancel_other_conversations(update, context)
    __show_nas_health_status(update.message)
    return RELOADABLE_STATE


@user_owner
@send_typing_action
def __bot_health_status(update, context):
    cancel_other_conversations(update, context)
    update.message.reply_text("The fact that I can reply to you means I'm good! Thanks for asking.")


@user_owner
def __reload_reloadable(update, context):
    query = update.callback_query
    data = query.data
    query.answer()
    if data == "resource_monitor":
        __show_resource_monitor(query, ACTION_EDIT)
    elif data == "nas_health":
        __show_nas_health_status(query, ACTION_EDIT)


def __show_nas_network_status(message, action=ACTION_REPLY):
    network_status = sys_info.network_status()
    vpn_status = sys_info.network_vpn_pptp()  # we can add the openVPN checks
    server_name = network_status["data"]["server_name"]
    dns_primary = network_status["data"]["dns_primary"]
    dns_secondary = network_status["data"]["dns_secondary"]
    ip = network_status["data"]["gateway_info"]["ip"]
    vpn = vpn_status["data"]

    reply_text = "*Server Name:*` {0}`\n".format(server_name)
    # DNS Primary is a must, or else there's no Telegram Bot
    reply_text += "*DNS Primary:*` {0}`\n".format(dns_primary)
    if len(dns_secondary) > 0:
        reply_text += "*DNS Secondary:*` {0}`\n".format(dns_secondary)
    # We should be able to get at least one ip
    reply_text += "*IP Address:*` {0}`\n".format(ip)
    if len(vpn) > 0:
        reply_text += "*VPN:*` Yes`\n"
    else:
        reply_text += "*VPN:*` No`\n"

    keyboard = [[InlineKeyboardButton("Reload", callback_data="nas_network")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if action == ACTION_EDIT:
        message.edit_message_text(text=escape_reserved_character(reply_text),
                                  parse_mode=ParseMode.MARKDOWN_V2,
                                  reply_markup=reply_markup)
    else:
        message.reply_text(text=escape_reserved_character(reply_text),
                           parse_mode=ParseMode.MARKDOWN_V2,
                           reply_markup=reply_markup)


def __show_resource_monitor(message, action=ACTION_REPLY):
    util = sys_info.utilisation()["data"]

    user_load = util["cpu"]["user_load"]
    system_load = util["cpu"]["system_load"]
    other_load = util["cpu"]["other_load"]
    reply_text = "*CPU Utilization*\n"
    reply_text += "`User     : {}%`\n".format(user_load)
    reply_text += "`System   : {}%`\n".format(user_load)
    reply_text += "`I/O Wait : {}%`\n\n".format(user_load)

    real_usage = util["memory"]["real_usage"]
    swap_usage = util["memory"]["swap_usage"]
    reply_text += "*Memory Utilization*\n"
    reply_text += "`Physical : {}%`\n".format(real_usage)
    reply_text += "`Swap     : {}%`\n\n".format(swap_usage)

    total_disk_utilization = util["disk"]["total"]["utilization"]
    disks = util["disk"]["disk"]
    reply_text += "*Disk Utilization*\n"
    disks_util = {}
    for disk in disks:
        display_name = disk["display_name"]
        utilization = disk["utilization"]
        disks_util[display_name] = utilization
    disks_util.update({"Total": total_disk_utilization})
    longest_display_name_length = 0
    for key in disks_util:
        length = len(key)
        if length > longest_display_name_length:
            longest_display_name_length = length
    longest_display_name_length += 1
    for name, util in disks_util.items():
        name_padded = name
        for i in range(longest_display_name_length - len(name)):
            name_padded += " "
        reply_text += "`{0}: {1}%`\n".format(name_padded, util)

    update_time = time.strftime("%d %B %Y %H:%M:%S", time.localtime(time.time()))
    reply_text += "\nLast update: {}".format(update_time)

    keyboard = [[InlineKeyboardButton("Reload", callback_data="resource_monitor")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if action == ACTION_EDIT:
        message.edit_message_text(text=escape_reserved_character(reply_text),
                                  parse_mode=ParseMode.MARKDOWN_V2,
                                  reply_markup=reply_markup)
    else:
        message.reply_text(text=escape_reserved_character(reply_text),
                           parse_mode=ParseMode.MARKDOWN_V2,
                           reply_markup=reply_markup)


def __show_nas_health_status(message, action=ACTION_REPLY):
    dsm_info = dsm.get_info()["data"]
    storage = strg.storage()["data"]
    update_available = sys_info.sys_upgrade_check()["data"]["update"]["available"]

    version = dsm_info["version_string"]
    temperature = dsm_info["temperature"]
    temperature_warn = dsm_info["temperature_warn"]
    temperature_status = "Not Good" if temperature_warn else "Good"
    update_status = "Update available" if update_available else "Latest"
    reply_text = "*Status*\n"
    reply_text += "`DSM Version        : {0} ({1})`\n".format(version[4:], update_status)
    reply_text += "`System Temperature : {0} °C ({1})`\n".format(temperature, temperature_status)

    reply_text += "\n*Storage Volume*\n"
    volumes = storage["volumes"]
    for volume in volumes:
        id = volume["id"].capitalize().replace("_", " ")
        status = volume["status"].capitalize()
        total = int(volume["size"]["total"])
        used = int(volume["size"]["used"])
        available = total - used
        reply_text += "`{0} ({1})`\n".format(id, status)
        reply_text += "`├─Total     : {}`\n".format(human_readable_size(total))
        reply_text += "`├─Used      : {}`\n".format(human_readable_size(used))
        reply_text += "`└─Available : {}`\n".format(human_readable_size(available))

    reply_text += "\n*Uptime*\n"
    uptime_seconds = int(dsm_info["uptime"])
    uptime_day = uptime_seconds // (24 * 3600)
    uptime_seconds = uptime_seconds % (24 * 3600)
    uptime_hour = uptime_seconds // 3600
    uptime_seconds %= 3600
    uptime_minutes = uptime_seconds // 60
    uptime_seconds %= 60
    seconds = uptime_seconds

    processed_date_reply = str()
    if uptime_day == 1:
        processed_date_reply = "{0} day ".format(uptime_day)
    elif uptime_day > 0:
        processed_date_reply = "{0} days ".format(uptime_day)

    reply_text += ("`{0}{1}:{2}:{3}`".format(processed_date_reply,
                                             "{0:0=2d}".format(int(uptime_hour)),
                                             "{0:0=2d}".format(int(uptime_minutes)),
                                             "{0:0=2d}".format(int(seconds))))

    update_time = time.strftime("%d %B %Y %H:%M:%S", time.localtime(time.time()))
    reply_text += "\n\nLast update: {}".format(update_time)

    keyboard = [[InlineKeyboardButton("Reload", callback_data="nas_health")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if action == ACTION_EDIT:
        message.edit_message_text(text=escape_reserved_character(reply_text),
                                  parse_mode=ParseMode.MARKDOWN_V2,
                                  reply_markup=reply_markup)
    else:
        message.reply_text(text=escape_reserved_character(reply_text),
                           parse_mode=ParseMode.MARKDOWN_V2,
                           reply_markup=reply_markup)


nas_network_handler = ConversationHandler(
    entry_points=[CommandHandler("nasnetwork", __nas_network_status)],
    states={
        RELOADABLE_STATE: [CallbackQueryHandler(__reload_reloadable)]
    },
    fallbacks=[],
    allow_reentry=True
)
resource_monitor_handler = ConversationHandler(
    entry_points=[CommandHandler("resourcemonitor", __resource_monitor)],
    states={
        RELOADABLE_STATE: [CallbackQueryHandler(__reload_reloadable)]
    },
    fallbacks=[],
    allow_reentry=True
)
nas_health_handler = ConversationHandler(
    entry_points=[CommandHandler("nashealth", __nas_health_status)],
    states={
        RELOADABLE_STATE: [CallbackQueryHandler(__reload_reloadable)]
    },
    fallbacks=[],
    allow_reentry=True
)
bot_health_handler = CommandHandler("bothealth", __bot_health_status)

dispatcher.add_handler(nas_network_handler)
dispatcher.add_handler(resource_monitor_handler)
dispatcher.add_handler(nas_health_handler)
dispatcher.add_handler(bot_health_handler)

__help__ = """*System Info*
/resourcemonitor - show NAS resource infos
/nasnetwork - show NAS network status
/nashealth - show NAS health status
/bothealth - show bot health status

"""
