from math import ceil
from synology_api.downloadstation import DownloadStation
from syno_bot import dispatcher, NAS_IP, NAS_PORT, DSM_ACCOUNT, DSM_PASSWORD
from syno_bot.modules import ACTION_EDIT, ACTION_REPLY
from syno_bot.modules.helper.bot_decorator import send_typing_action
from syno_bot.modules.helper.conversation import cancel_other_conversations
from syno_bot.modules.helper.file_size import human_readable_size
from syno_bot.modules.helper.user_status import user_owner
from syno_bot.modules.helper.string_processor import escape_reserved_character
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, ParseMode
from telegram.ext import (CallbackQueryHandler, CommandHandler, ConversationHandler, Filters,
                          MessageHandler)
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown

import telegram
import time

instance = DownloadStation.login(DSM_ACCOUNT, DSM_PASSWORD, NAS_IP, NAS_PORT)

DOCUMENT_OR_LINK = range(1)

MAIN_PAGE, DETAIL_PAGE, REMOVE_CONFIRMATION_PAGE = range(3)

FIRST, PREVIOUS, NEXT, LAST = range(4)
PAGE_LIMIT = 5
TASK_PAGE_EMPTY_STATE = "You have no download task. Use /adddownload to create a new one."
TASK_PAGE_HEADER_TEMPLATE = "Page *{0}* of *{1}* - You have *{2}* download task"
TASK_LIST_TEMPLATE = """*Task #{0}:*` {1}`
*Status:*` {2} ({3:.2f}%)`

"""
TASK_PAGE_FOOTER = "Choose a task from the list below to see its details:"
PAGE_CALLBACK_DATA = "page_"
DETAILS_CALLBACK_DATA = "details_"

DETAIL_RESUME = "resume_"
DETAIL_PAUSE = "pause_"
DETAIL_REMOVE = "remove_"
DETAIL_BACK = "back"

CONFIRMATION_PAGE_TEXT_TEMPLATE = "Remove task for `{0}`?"
CONFIRMATION_YES = "y_"
CONFIRMATION_NO = "n_"

RELOAD = "RELOAD_"

def __get_task_list_size():
    return instance.tasks_list()["data"]["total"]


def __get_task_title(task_id):
    return instance.tasks_info(task_id)["data"]["tasks"][0]["title"]


@send_typing_action
def __add_download_link(update, context):
    message = update.message
    if message.document:
        link = message.document.get_file().file_path
    elif message.audio:
        link = message.audio.get_file().file_path
    elif message.photo:
        i_width = -1
        for photo_size in message.photo:
            if photo_size.width > i_width:
                i_width = photo_size.width
                to_download = photo_size

        if not to_download:
            message.reply_text("Failed to get item. Please try again.")
            return ConversationHandler.END

        link = to_download.get_file().file_path
    elif message.video:
        link = message.video.get_file().file_path
    else:
        link = message.text

    if __handle_link(update.message, link):
        return ConversationHandler.END
    else:
        return DOCUMENT_OR_LINK


def __handle_link(message, link):
    try:
        instance.tasks_create(link)
        message.reply_text("Item added successfully.")
        return True
    except:
        message.reply_text("Failed to add item. Please try again.")
        return False


def __cancel(update, context):
    update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END


def __download_list_data(message, page_number=1, action=ACTION_REPLY):
    # List 5 tasks per page
    total_tasks_size = __get_task_list_size()
    if total_tasks_size == 0:
        message.reply_text(TASK_PAGE_EMPTY_STATE)
        return ConversationHandler.END

    total_page = ceil(total_tasks_size / PAGE_LIMIT)
    offset_val = (page_number - 1) * PAGE_LIMIT
    task_list = instance.tasks_list(offset=offset_val, limit=PAGE_LIMIT)
    reply_text = TASK_PAGE_HEADER_TEMPLATE.format(page_number, total_page, total_tasks_size)
    if total_tasks_size > 1:
        reply_text += "s"

    reply_text += ".\n\n"
    buttons = []
    task_number = offset_val + 1
    for current in task_list["data"]["tasks"]:
        progress = 0
        if current["size"] != 0:
            progress = current["additional"]["transfer"]["size_downloaded"] / current["size"] * 100

        reply_text += TASK_LIST_TEMPLATE.format(task_number,
                                                current["title"],
                                                current["status"].capitalize(),
                                                progress)
        buttons.append(InlineKeyboardButton(task_number,
                                            callback_data=DETAILS_CALLBACK_DATA + current["id"]))
        task_number += 1

    previous_page = page_number - 1
    if previous_page < 1:
        previous_page = 1

    next_page = page_number + 1
    if next_page > total_page:
        next_page = total_page

    reply_text += TASK_PAGE_FOOTER
    keyboard = [buttons]
    if total_page > 1:
        keyboard.append(
            [InlineKeyboardButton("<<", callback_data=PAGE_CALLBACK_DATA + "1"),
             InlineKeyboardButton("<", callback_data=PAGE_CALLBACK_DATA + str(previous_page)),
             InlineKeyboardButton(">", callback_data=PAGE_CALLBACK_DATA + str(next_page)),
             InlineKeyboardButton(">>", callback_data=PAGE_CALLBACK_DATA + str(total_page))]
        )

    keyboard.append([InlineKeyboardButton("Reload", callback_data=RELOAD + str(page_number))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if action == ACTION_REPLY:
        message.reply_text(text=escape_reserved_character(reply_text),
                                  parse_mode=ParseMode.MARKDOWN_V2,
                                  reply_markup=reply_markup)
    elif action == ACTION_EDIT:
        message.edit_message_text(text=escape_reserved_character(reply_text),
                                  parse_mode=ParseMode.MARKDOWN_V2,
                                  reply_markup=reply_markup)


def __list_page_change(update, context):
    query = update.callback_query
    query.answer()
    page_number = int(query.data.split("_")[1])
    __download_list_data(query, page_number=page_number, action=ACTION_EDIT)


def __open_details_page(update, context):
    query = update.callback_query
    task_id = query.data.split(DETAILS_CALLBACK_DATA)[1]
    __show_details_page(query, task_id)
    return DETAIL_PAGE


def __show_details_page(query, task_id):
    task_info = instance.tasks_info(task_id)["data"]["tasks"][0]
    task_active = task_info["status"] != "finished" and task_info["status"] != "paused"
    task_bt = task_info["type"] == "bt"

    title = task_info["title"]
    status = task_info["status"].capitalize()
    progress = 0
    if task_info["size"] != 0:
        progress = task_info["additional"]["transfer"]["size_downloaded"] / task_info["size"] * 100
    ul_speed = human_readable_size(task_info["additional"]["transfer"]["speed_upload"]) + "/s"
    dl_speed = human_readable_size(task_info["additional"]["transfer"]["speed_download"]) + "/s"
    uled_size = human_readable_size(task_info["additional"]["transfer"]["size_uploaded"])
    dled_size = human_readable_size(task_info["additional"]["transfer"]["size_downloaded"])
    total_size = human_readable_size(task_info["size"])
    source = task_info["additional"]["detail"]["uri"]
    created_time = time.strftime("%d %B %Y %H:%M",
                                 time.localtime(task_info["additional"]["detail"]["create_time"]))
    update_time = time.strftime("%d %B %Y %H:%M:%S", time.localtime(time.time()))

    reply_text = "*Name:* `{}`\n".format(title)
    reply_text += "*Status:*` {} ({:.2f}%)`\n".format(status, progress)
    if task_active:
        if task_bt:
            reply_text += "*Transfer Speed (UL|DL):*` {0}|{1}`\n".format(ul_speed, dl_speed)
        else:
            reply_text += "*Transfer Speed (DL):*` {}`\n".format(dl_speed)

    if task_bt:
        reply_text += "*Size (UL|DL|Total):*` {0}|{1}|{2}`\n".format(uled_size,
                                                                     dled_size,
                                                                     total_size)
    else:
        reply_text += "*Size (DL|Total):*` {0}|{1}`\n".format(dled_size, total_size)

    reply_text += "*Created time:*` {}`\n".format(created_time)
    reply_text += "*Source:*` {}`\n\n".format(source)
    reply_text += "Last update: {}".format(update_time)

    keyboard = []
    if task_info["status"] != "finished":
        if task_info["status"] == "paused":
            callback_data = DETAIL_RESUME + task_id + "&" + DETAILS_CALLBACK_DATA + task_id
            keyboard.append([InlineKeyboardButton("Resume task",callback_data=callback_data)])
        elif task_info["status"] != "error":
            callback_data = DETAIL_PAUSE + task_id + "&" + DETAILS_CALLBACK_DATA + task_id
            keyboard.append([InlineKeyboardButton("Pause task", callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("Remove task", callback_data=DETAIL_REMOVE + task_id)])
    keyboard.append([InlineKeyboardButton("Reload", callback_data=RELOAD + task_id)])
    keyboard.append([InlineKeyboardButton("« Back to list", callback_data=DETAIL_BACK)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    query.edit_message_text(text=escape_reserved_character(reply_text),
                            parse_mode=ParseMode.MARKDOWN_V2,
                            reply_markup=reply_markup)


def __details_page_handler(update, context):
    query = update.callback_query
    data = query.data
    if data.startswith(DETAIL_RESUME):
        task_id = (data.split(DETAIL_RESUME)[1]).split("&")[0]
        instance.resume_task(task_id)
        time.sleep(1)
        __show_details_page(query, task_id)
        return DETAIL_PAGE
    elif data.startswith(DETAIL_PAUSE):
        task_id = (data.split(DETAIL_PAUSE)[1]).split("&")[0]
        instance.pause_task(task_id)
        time.sleep(1)
        __show_details_page(query, task_id)
        return DETAIL_PAGE
    elif data.startswith(RELOAD):
        task_id = data.split(RELOAD)[1]
        __show_details_page(query, task_id)
    elif data.startswith(DETAIL_REMOVE):
        # Send confirmation before removing
        task_id = data.split(DETAIL_REMOVE)[1]
        __show_remove_confirmation(query, task_id)
        return REMOVE_CONFIRMATION_PAGE
    elif data == DETAIL_BACK:
        query.answer()
        __download_list_data(query, page_number=1, action=ACTION_EDIT)
        return MAIN_PAGE


def __show_remove_confirmation(query, task_id):
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=CONFIRMATION_YES + task_id)],
        [InlineKeyboardButton("No", callback_data=CONFIRMATION_NO + task_id)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.answer()
    reply_text = CONFIRMATION_PAGE_TEXT_TEMPLATE.format(__get_task_title(task_id))
    query.edit_message_text(text=escape_reserved_character(reply_text),
                            parse_mode=ParseMode.MARKDOWN_V2,
                            reply_markup = reply_markup)


def __remove_task_confirmation_page_handler(update, context):
    query = update.callback_query
    data = query.data
    if data.startswith(CONFIRMATION_YES):
        task_id = data.split(CONFIRMATION_YES)[1]
        instance.delete_task(task_id)
        time.sleep(1)
        query.answer()
        __download_list_data(query, page_number=1, action=ACTION_EDIT)
        return MAIN_PAGE
    elif data.startswith(CONFIRMATION_NO):
        task_id = data.split(CONFIRMATION_NO)[1]
        __show_details_page(query, task_id)
        return DETAIL_PAGE


@user_owner
@send_typing_action
def __resume_downloads(update, context):
    task_list = instance.tasks_list()
    resumed_count = 0
    for current in task_list["data"]["tasks"]:
        result = instance.resume_task(current["id"])
        if result["success"] == True:
            resumed_count += 1

    update.message.reply_text("Successfully resumed {} download(s).".format(resumed_count))


@user_owner
@send_typing_action
def __pause_downloads(update, context):
    task_list = instance.tasks_list()
    paused_count = 0
    for current in task_list["data"]["tasks"]:
        result = instance.pause_task(current["id"])
        if result["success"] == True:
            paused_count += 1

    update.message.reply_text("Successfully paused {} download(s).".format(paused_count))


@user_owner
@send_typing_action
def __cleanup_downloads(update, context):
    cancel_other_conversations(update, context)
    keyboard = [
        [InlineKeyboardButton("Yes", callback_data=CONFIRMATION_YES)],
        [InlineKeyboardButton("No", callback_data=CONFIRMATION_NO)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text="Are you sure?",
                              reply_markup = reply_markup)
    return REMOVE_CONFIRMATION_PAGE


@send_typing_action
def __cleanup_confirmation_page_handler(update, context):
    query = update.callback_query
    data = query.data
    if data == CONFIRMATION_YES:
        task_list = instance.tasks_list()
        removed_count = 0
        for current in task_list["data"]["tasks"]:
            if current["status"] == "finished":
                result = instance.delete_task(current["id"])
                if result["success"] == True:
                    removed_count += 1

        reply_text = "Successfully removed {} download(s).".format(removed_count)
    elif data == CONFIRMATION_NO:
        reply_text = "Operation cancelled."

    query.answer()
    query.edit_message_text(reply_text)
    return ConversationHandler.END


@user_owner
@send_typing_action
def __list_downloads(update, context):
    cancel_other_conversations(update, context)
    __download_list_data(update.message)
    return MAIN_PAGE


@user_owner
def __add_download_entry(update, context):
    cancel_other_conversations(update, context)
    update.message.reply_text("Send me something for me to download. " +
                              "Keep in mind that I can process only one thing at a time.")
    return DOCUMENT_OR_LINK


resume_handler = CommandHandler("resumedownloads", __resume_downloads)
pause_handler = CommandHandler("pausedownloads", __pause_downloads)
cancel_handler = CommandHandler("cancel", __cancel)

cleanup_handler = ConversationHandler(
    entry_points=[CommandHandler("cleanupdownloads", __cleanup_downloads)],
    states={
        REMOVE_CONFIRMATION_PAGE: [CallbackQueryHandler(__cleanup_confirmation_page_handler),
                                   cancel_handler]
    },
    fallbacks=[cancel_handler],
    allow_reentry=True
)
list_downloads_handler = ConversationHandler(
    entry_points=[CommandHandler("mydownloads", __list_downloads)],
    states={
        MAIN_PAGE: [CallbackQueryHandler(__list_page_change, pattern=PAGE_CALLBACK_DATA),
                    CallbackQueryHandler(__open_details_page, pattern=DETAILS_CALLBACK_DATA),
                    CallbackQueryHandler(__list_page_change, pattern=RELOAD)],
        DETAIL_PAGE: [CallbackQueryHandler(__details_page_handler)],
        REMOVE_CONFIRMATION_PAGE: [CallbackQueryHandler(__remove_task_confirmation_page_handler),
                                   cancel_handler]
    },
    fallbacks=[cancel_handler],
    allow_reentry=True
)
add_download_handler = ConversationHandler(
    entry_points=[CommandHandler("adddownload", __add_download_entry)],
    states={
        DOCUMENT_OR_LINK: [MessageHandler(Filters.audio | Filters.video | Filters.photo |
                                          Filters.document | Filters.text &
                                          (Filters.entity(MessageEntity.URL) |
                                          Filters.entity(MessageEntity.TEXT_LINK)),
                                          __add_download_link)]
    },
    fallbacks=[cancel_handler],
    allow_reentry=True
)


dispatcher.add_handler(resume_handler)
dispatcher.add_handler(pause_handler)
dispatcher.add_handler(cleanup_handler)
dispatcher.add_handler(list_downloads_handler)
dispatcher.add_handler(add_download_handler)

__help__ = """*Download Station*
/mydownloads - manage your downloads
/adddownload - create a new download task
/resumedownloads - resume all inactive download tasks
/pausedownloads - pause all active download tasks
/cleanupdownloads - clear completed download tasks

"""
