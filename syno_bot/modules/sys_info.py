import time

from synology_api.sys_info import SysInfo
from syno_bot import dispatcher, NAS_IP, NAS_PORT, DSM_ACCOUNT, DSM_PASSWORD
from syno_bot.modules.helper.bot_decorator import send_typing_action
from syno_bot.modules.helper.file_size import human_readable_size
from syno_bot.modules.helper.user_status import user_owner
from syno_bot.modules.helper.string_processor import escape_reserved_character
from telegram import ParseMode
from telegram.ext import CommandHandler

instance = SysInfo.login(DSM_ACCOUNT, DSM_PASSWORD, NAS_IP, NAS_PORT)

@user_owner
@send_typing_action
def __nas_network_status(update, context):
    network_status = instance.network_status()
    vpn_status = instance.network_vpn_pptp()  # we can add the openVPN checks
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

    update.message.reply_text(text=escape_reserved_character(reply_text),
                              parse_mode=ParseMode.MARKDOWN_V2)


@user_owner
@send_typing_action
def __nas_health_status(update, context):
    util = instance.utilisation()["data"]
    storage = instance.storage()["data"]
    print(str(storage))

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
    if longest_display_name_length < 9:
        longest_display_name_length = 9 # So much for aligning
    for name, util in disks_util.items():
        name_padded = name
        for i in range(longest_display_name_length - len(name)):
            name_padded += " "
        reply_text += "`{0}: {1}%`\n".format(name_padded, util)

    reply_text += "\n*Storage Utilization*\n"
    volumes = storage["volumes"]
    for volume in volumes:
        total = int(volume["size"]["total"])
        used = int(volume["size"]["used"])
        available = total - used
        reply_text += "`{}`\n".format(volume["id"])
        reply_text += "`Total     : {}`\n".format(human_readable_size(total))
        reply_text += "`Used      : {}`\n".format(human_readable_size(used))
        reply_text += "`Available : {}`\n\n".format(human_readable_size(available))

    update_time = time.strftime("%d %B %Y %H:%M:%S", time.localtime(time.time()))
    reply_text += "Last update: {}".format(update_time)

    update.message.reply_text(text=escape_reserved_character(reply_text),
                             parse_mode=ParseMode.MARKDOWN_V2)


@user_owner
@send_typing_action
def __bot_health_status(update, context):
    update.message.reply_text("I'm good! Thanks for asking.")


nas_network_handler = CommandHandler("nasnetwork", __nas_network_status)
nas_health_handler = CommandHandler("nashealth", __nas_health_status)
bot_health_handler = CommandHandler("bothealth", __bot_health_status)

dispatcher.add_handler(nas_network_handler)
dispatcher.add_handler(nas_health_handler)
dispatcher.add_handler(bot_health_handler)

__help__ = """*System Info*
/nasnetwork - show NAS network status
/nashealth - show NAS health status
/bothealth - show bot health status

"""
