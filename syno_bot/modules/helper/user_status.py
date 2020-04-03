from functools import wraps
from syno_bot import BOT_OWNER_ID

def user_owner(func):
    @wraps(func)
    def is_owner(update, context, *args, **kwargs):
        user = update.effective_user
        if str(user.id) == BOT_OWNER_ID:
            return func(update, context, *args, **kwargs)
        elif not user:
            pass
        else:
            update.message.reply_text("I have no obligation to serve you.")

    return is_owner


def user_pm(func):
    @wraps(func)
    def is_pm(update, context, *args, **kwargs):
        chat = update.effective_chat
        if chat.type == "private":
            return func(update, context, *args, **kwargs)
        elif not chat:
            pass
        else:
            update.message.reply_text("I'm afraid to tell you that it's a PM only command.")

    return is_pm
