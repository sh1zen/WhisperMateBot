from telegram import Update
from telegram.ext import ContextTypes

from utils.ModuleBase import ModuleBase
from utils.keyboards import KeyboardType, getKeyboard
from workers.locale_handler import __


class Actions(ModuleBase):

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        await context.bot.send_message(
            text=__("<b>Choose you action</b>", user_id),
            chat_id=update.effective_chat.id,
            reply_markup=getKeyboard(KeyboardType.ACTIONS, user_id)
        )
