import sys

from Crypto.Random.random import randint
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from utils.ModuleBase import ModuleBase
from workers.accessibility import send_typing_action
from workers.locale_handler import __


class Random(ModuleBase):

    def register_handlers(self, keyboard=None):
        self.app.add_handler(CommandHandler("random", self.handler))

    @send_typing_action
    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        cmd = update.message.text.lower().split()

        if len(cmd) == 2:
            max_range = int(cmd[1])
        else:
            max_range = sys.maxsize

        rand = randint(0, max_range)
        await update.message.reply_text(__("Random value is: {}", update.effective_user.id, str(rand)))
