from syno_bot import dispatcher
from telegram.ext import ConversationHandler

def cancel_other_conversations(update, context):
    """Cancel other conversations so that it doesn't pick up response from new conversation"""
    all_hand = dispatcher.handlers
    for dict_group in all_hand:
        for handler in all_hand[dict_group]:
            if isinstance(handler, ConversationHandler):
                handler.update_state(ConversationHandler.END, handler._get_key(update))
