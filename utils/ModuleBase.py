from telegram import Update
from telegram.ext import ContextTypes, filters, MessageHandler, CommandHandler, Application, CallbackQueryHandler

from utils.keyboards import getKeyboard, KeyboardType
from utils.regexp import regexp
from utils.utility import slugify
from workers.accessibility import send_typing_action
from workers.bot import ChatState, StateHandler
from workers.locale_handler import _all, __


class ModuleBase(object):
    __slots__ = ['app', 'hook']

    priority = 10

    def __init__(self, app: Application):
        self.app = app
        self.hook = slugify(self.__class__.__name__)
        self.register_handlers()

    def register_handlers(self, keyboard=None):

        keyboard_hook = self.hook if keyboard is None else keyboard

        # add a StateHandler only if handled by child class
        if type(self).stateHandler != ModuleBase.stateHandler:
            self.app.add_handler(StateHandler(self.app, self.hook, self.stateHandler))

        # add a CallbackQueryHandler hook.callback only if handled by child class
        if type(self).callbackQueryHandler != ModuleBase.callbackQueryHandler:
            self.app.add_handler(CallbackQueryHandler(self.callbackQueryHandler, pattern=f"^{self.hook}."))

        # add CommandHandler and keyBoardCommandFilter handlers only if handled by child class
        if type(self).handler != ModuleBase.handler:
            self.app.add_handler(CommandHandler(self.hook, self.handler))
            self.app.add_handler(MessageHandler(self.keyBoardCommandFilter(keyboard_hook), self.handler))

    @send_typing_action
    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ Handle main callback. """
        pass

    @send_typing_action
    async def stateHandler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ Handle state-oriented callbacks. """
        await update.message.reply_text(
            "<b>Message Handler not set</b>",
            reply_markup=getKeyboard(KeyboardType.HOME, update.effective_user.id)
        )
        self.unset_state(context)

    async def callbackQueryHandler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ Handle callback-query callbacks. """
        pass

    async def home(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        await update.message.reply_text(
            __("<b><i>Resetting Home Keyboard</i></b>", user_id),
            reply_markup=getKeyboard(KeyboardType.HOME, user_id)
        )

    def commandRegex(self, name):
        return regexp("#^•(" + ('|'.join(_all(name))) + ").*•$#i", '#')

    def keyBoardCommandFilter(self, name):
        # todo refine emoji support
        return filters.TEXT & filters.Regex(self.commandRegex(name))

    def checkCallback(self, query: str, name: str, start=False):
        return query.startswith(f"{self.hook}.{name}") if start else query == f"{self.hook}.{name}"

    def set_state(self, context, state):
        return ChatState.set(context, name=self.hook, state=state)

    def unset_state(self, context):
        return ChatState.unset(context)

    def has_state(self, context, state):
        return ChatState.has(context, name=self.hook, state=state)
