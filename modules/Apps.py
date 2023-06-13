from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from utils.ModuleBase import ModuleBase
from utils.keyboards import KeyboardType, getKeyboard
from workers.locale_handler import __


class Apps(ModuleBase):

    def register_handlers(self, keyboard=None):
        self.app.add_handler(CommandHandler('apps', self.handler))
        super().register_handlers(keyboard)

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        await context.bot.send_message(
            text=__("<b>Tap on an app to start</b>", user_id),
            chat_id=update.effective_chat.id,
            reply_markup=getKeyboard(KeyboardType.APPS, user_id)
        )
