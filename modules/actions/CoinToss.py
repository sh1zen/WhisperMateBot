import random

from telegram import Update
from telegram.ext import ContextTypes

from utils.ModuleBase import ModuleBase
from workers.accessibility import send_typing_action
from workers.locale_handler import __


class CoinToss(ModuleBase):

    @send_typing_action
    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        await update.message.reply_text(random.choice(["🙃" + __("Heads", user_id), "❌" + __("Tails", user_id)]))
