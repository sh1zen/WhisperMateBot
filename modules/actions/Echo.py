from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

from utils.ModuleBase import ModuleBase
from utils.keyboards import getKeyboard, KeyboardType
from workers.accessibility import send_typing_action
from workers.locale_handler import __

ECHO_MODE = 1


class Echo(ModuleBase):
    priority = 0

    def register_handlers(self, keyboard=None):
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('echo', self.handler),
                MessageHandler(self.keyBoardCommandFilter('echo'), self.handler)
            ],
            states={
                ECHO_MODE: [
                    MessageHandler(filters.TEXT, self.echo)
                ],
            },
            fallbacks=[MessageHandler(filters.TEXT, self.echo)],
        )

        self.app.add_handler(conv_handler)

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        await update.message.reply_text(
            __("Write anything, I will just repeat it.", user_id),
            reply_markup=getKeyboard(KeyboardType.CANCEL, user_id)
        )
        return ECHO_MODE

    @send_typing_action
    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        message = update.message.text or ''

        if self.commandRegex('cancel').match(message):

            if ECHO_MODE:
                user_id = update.effective_user.id

                await update.message.reply_text(
                    __("Echo mode deactivated.", user_id),
                    reply_markup=getKeyboard(KeyboardType.ACTIONS, user_id)
                )
            return ConversationHandler.END

        await update.message.reply_text(message)
        return ECHO_MODE
