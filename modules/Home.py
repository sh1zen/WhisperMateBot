from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler

from config import BOT_NAME
from utils.ModuleBase import ModuleBase
from utils.keyboards import getKeyboard, KeyboardType
from workers.Database.DBUsers import DBUsers
from workers.locale_handler import __


class Home(ModuleBase):
    priority = 2

    def register_handlers(self, keyboard=None):
        self.app.add_handler(CommandHandler('start', self.start))
        self.app.add_handler(CommandHandler('home', self.home))
        self.app.add_handler(MessageHandler(self.keyBoardCommandFilter('back'), self.home))
        self.app.add_handler(MessageHandler(self.keyBoardCommandFilter('home'), self.home))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_id = user.id

        if update.message.text == '/start':
            DBUsers.insert({
                'user_id': user.id,
                'is_bot': user.is_bot,
                'chat_id': update.message.chat.id,
                'lang': user.language_code
            })

        await update.message.reply_text(
            __("<b>Welcome <i>{}</i> to {}</b>\n\n", user_id, user.username, BOT_NAME) +
            __("Up to now <b>{}</b> users are using this bot.\n", user_id, DBUsers.count()),
            reply_markup=getKeyboard(KeyboardType.HOME, user_id)
        )
