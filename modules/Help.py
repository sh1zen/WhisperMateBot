from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler
)

from utils.ModuleBase import ModuleBase
from utils.keyboards import KeyboardType, getKeyboard
from workers.Database.DBFeedbacks import DBFeedbacks
from workers.bot import save_media
from workers.locale_handler import __


class Help(ModuleBase):
    priority = 2

    def register_handlers(self, keyboard=None):
        self.app.add_handler(CommandHandler('about', self.handler))
        super().register_handlers(keyboard='about & help')

    async def handler(self, update, context):
        await update.message.reply_text(
            "Choose one of the following options:",
            reply_markup=getKeyboard(KeyboardType.HELP_INLINE, update.effective_user.id, self.hook)
        )

    async def stateHandler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id

        if self.commandRegex('cancel').match(update.message.text or ''):

            await update.message.reply_text(
                "👍",
                reply_markup=getKeyboard(KeyboardType.HOME, user_id)
            )
        elif self.has_state(context, 'feedback'):

            path = await save_media(update, context)

            DBFeedbacks.insert({
                'user_id': user_id,
                'message': update.message.text or '',
                'attachment': path
            })

            await update.message.reply_text(
                __("<b>👍 Feedback reported.</b>", user_id),
                reply_markup=getKeyboard(KeyboardType.HOME, user_id)
            )

        self.unset_state(context)

    async def callbackQueryHandler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        query_data = query.data

        user_id = update.effective_user.id

        if self.checkCallback(query_data, 'back'):
            await query.edit_message_text(
                text=__("Choose one of the following options:", user_id),
                reply_markup=getKeyboard(KeyboardType.HELP_INLINE, user_id, self.hook)
            )

        elif self.checkCallback(query_data, 'info'):
            await query.edit_message_text(
                text=__(
                    "With this bot you can chat with boy and girls choosing you preferences about age 📆 gender 👦👧 and distance 📍." +
                    "The chat is anonymous and the people you chat with have no way to understand who you really are!\n\n" +
                    "<i>Choose you preferences with  /settings\nReport users with  /report</i>\n\n" +
                    "<i>Spam and illegal stuff are forbidden and punished with ban. Read more about under Term of Services</i>",
                    user_id
                ),
                reply_markup=getKeyboard(KeyboardType.BACK_INLINE, user_id, self.hook)
            )

        elif self.checkCallback(query_data, 'tos'):
            await query.edit_message_text(
                text=__(
                    "<b>TERMS OF SERVICE:</b>\n\n" +
                    "By using ChatIncognitoBot you agree that:\n" +
                    "- you will not make any illegal stuff\n" +
                    "- you will not share illegal pornographic contents (e.g. child porn, revenge porn)\n" +
                    "- you will not promote violence\n" +
                    "- you will not send spam\n" +
                    "- you will not make scam\n" +
                    "- you will use our /report command if you see something that violates our Terms of service.\n" +
                    "We reserve the right to update this terms of services later.\n\n" +
                    "<b>we will take actions against users violating our term of service and ban them.</b>",
                    user_id
                ),
                reply_markup=getKeyboard(KeyboardType.BACK_INLINE, user_id, self.hook)
            )

        elif self.checkCallback(query_data, 'feedback'):
            await query.message.reply_text(
                __(
                    "<b>Reporting feedback, to cancel this operation press Cancel button.</b>\n\n" +
                    "<i>You can send text or any kind of media. If you are in a chat, replying to this message your message won't be sent to the user you're chatting with, but only to us.</i>",
                    user_id
                ),
                reply_markup=getKeyboard(KeyboardType.CANCEL, user_id)
            )
            self.set_state(context, 'feedback')

        elif self.checkCallback(query_data, 'about'):
            await query.message.edit_text(
                __("<b>📌 Developed by @sh1zen.</b>", user_id),
                reply_markup=getKeyboard(KeyboardType.ABOUT_INLINE, user_id, self.hook)
            )
