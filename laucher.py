try:
    from telegram import __version_info__, __version__, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This bot requires is not compatible with your current PTB version {__version__}."
    )

import asyncio
from config import TELEGRAM_BOT_TOKEN
import logging


from telegram.constants import ParseMode
from telegram import Update
from telegram.ext import (
    Application,
    PicklePersistence,
    filters, ContextTypes, MessageHandler, Defaults, ConversationHandler
)

from utils.keyboards import getKeyboard, KeyboardType
from workers.constants import WMB_ABS_PATH
from workers.bot import post_init, post_shutdown, schedules_handler, ChatState
from workers.accessibility import send_typing_action
from workers.locale_handler import Localizer, __
from utils.utility import auto_loader

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def load_modules(app, cdir='./modules/'):
    modules_init = []

    modules = sorted(
        auto_loader(cdir),
        key=lambda x: getattr(getattr(x, x.__name__.split(".")[-1].strip()), 'priority')
    )

    # Iterate over the files
    for module in modules:
        modules_init.append(getattr(module, module.__name__.split(".")[-1].strip())(app))

    return modules_init


@send_typing_action
async def handle_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("<i>Sorry but your request was not understood.</i>")
    print(update)


@send_typing_action
async def reset_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        __("<b><i>Resetting Home Keyboard</i></b>", user_id),
        reply_markup=getKeyboard(KeyboardType.HOME, user_id)
    )
    ChatState.unset(context)
    return ConversationHandler.END


def main() -> None:

    Localizer().install()

    defaults = Defaults(parse_mode=ParseMode.HTML, disable_web_page_preview=True, block=True)

    persistence = PicklePersistence(filepath=f"{WMB_ABS_PATH}/data/conversations")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).defaults(defaults).persistence(persistence).post_init(
        post_init).build()

    app.add_handler(MessageHandler(filters.Regex(r'^/home$'), reset_handler))

    modules = load_modules(app)

    print("{} modules loaded..".format(len(modules)))

    # todo remove after debug
    app.add_handler(MessageHandler(filters.ALL, handle_request))

    schedules_handler(app)

    # Run the bot until the user presses Ctrl-C
    app.run_polling(close_loop=False)

    asyncio.get_event_loop().run_until_complete(post_shutdown(app))


if __name__ == "__main__":
    main()
