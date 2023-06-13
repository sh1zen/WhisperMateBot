import re
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler, Application

from utils.ModuleBase import ModuleBase
from utils.teleapi import send_text
from utils.utility import parse_time, md5
from workers.Database.DBSchedules import DBSchedules
from workers.locale_handler import __


class Alarm(ModuleBase):

    def register_handlers(self, keyboard=None):
        self.app.add_handler(CommandHandler('alarm', self.set_handler))
        self.app.add_handler(CommandHandler('alarmslist', self.list_handler))
        self.app.add_handler(CallbackQueryHandler(self.callbackQueryHandler, pattern=f"^{self.hook}."))

    async def callbackQueryHandler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query

        job_id = query.data.split(".")[-1].strip()

        DBSchedules.delete({'id': job_id})

        alarms = self.get_jobs(update.effective_chat.id)
        user_id = update.effective_user.id

        if len(alarms) == 0:
            await query.edit_message_text(
                __("<b>No alarms set found.</b>", user_id)
            )
        else:
            await query.edit_message_text(
                __("<b>Tap on the alarm you want to remove:</b>", user_id),
                reply_markup=InlineKeyboardMarkup(alarms)
            )

    async def set_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id

        try:
            chat_id = str(update.effective_message.chat_id)

            matches = re.findall(
                r'^(\d+|(\d{1,2}-\d{1,2}(-(\d{2}|\d{4}))?)?\s+(\d{1,2}:\d{2}(:\d{2})?))\s+(.+)$',
                ' '.join(context.args).strip()
            )

            matched_tuple = matches[0] or ()

            time_sec = parse_time(matched_tuple[0], False)

            if time_sec < 0 or not time_sec:
                raise Exception("invalid time")

            reminder = matched_tuple[6].strip()

            name = md5(chat_id + matched_tuple[0] + reminder)

            DBSchedules.insert({
                'name': name,
                'reminder': reminder,
                'timestamp': time_sec,
                'chat_id': chat_id,
                'handler': 'modules.actions.Alarm.beep'
            })

            await update.effective_message.reply_text(__("Timer successfully set!", user_id))

        except Exception:
            await update.effective_message.reply_text(
                __("Usage: /set [seconds | (YYYY-)MM-DD HH:MM:SS | HH:MM:SS] [reminder]", user_id)
            )

    async def list_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id

        alarms = self.get_jobs(update.message.chat_id)

        if len(alarms) == 0:
            await update.message.reply_text(
                __("<b>No alarms set found.</b>", user_id)
            )
        else:
            await update.message.reply_text(
                __("<b>Tap on the alarm you want to remove:</b>", user_id),
                reply_markup=InlineKeyboardMarkup(alarms)
            )

    def get_jobs(self, chat_id=None):
        alarms_list = []

        for job in DBSchedules.get_rows({'chat_id': chat_id}):
            alarms_list.append(
                [
                    InlineKeyboardButton(
                        "⏰ " + datetime.fromtimestamp(job['timestamp']).strftime("%Y-%m-%d %H:%M:%S"),
                        callback_data=f"{self.hook}.{job['id']}"
                    )
                ]
            )

        return alarms_list

    @staticmethod
    def beep(schedule, app: Application) -> None:
        """Send the alarm message."""
        DBSchedules.delete({'id': schedule['id']})
        send_text(schedule['chat_id'], schedule['reminder'])
