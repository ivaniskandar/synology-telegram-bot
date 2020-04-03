from syno_bot import dispatcher, updater, LOGGER, START_MESSAGE
from syno_bot.modules.helper.user_status import user_owner
from syno_bot.modules.helper.string_processor import escape_reserved_character
from telegram import ParseMode
from telegram.ext import CommandHandler, MessageHandler, Filters

@user_owner
def start(update, context):
    update.message.reply_text(text=escape_reserved_character(START_MESSAGE),
                            parse_mode=ParseMode.MARKDOWN_V2)


@user_owner
def cancel(update, context):
    # Default cancel response
    update.message.reply_text("What to cancel? I'm not doing anything right now.")


@user_owner
def unknown(update, context):
    update.message.reply_text("I'm sorry, I don't understand what were you trying to tell me.")


def error(update, context):
    try:
        raise context.error
    except Exception as e:
        LOGGER.critical(e, exc_info=True)

def main():
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("cancel", cancel))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    # log all errors
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    LOGGER.info("Bot started successfully. Have a nice day.")

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
