from telegram import Update
from telegram.ext import ContextTypes

from utils.ModuleBase import ModuleBase


class CryptoCoin(ModuleBase):

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass
