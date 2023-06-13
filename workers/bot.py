import datetime
import importlib
import time
from typing import List, Tuple, Union, Optional, Any, Dict

from telegram import BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.ext._utils.types import CCT, HandlerCallback, RT

from utils.utility import unique_file_name, synchronize_function
from workers.Database.DBSchedules import DBSchedules
from workers.Database.Database import Database
from workers.constants import WMB_ABS_PATH


class ChatState:
    @staticmethod
    def set(context: ContextTypes.DEFAULT_TYPE, name, state):
        if context:
            context.user_data['CHAT_STATE'] = name + "|" + str(state)
            return True

        return False

    @staticmethod
    def get(context: ContextTypes.DEFAULT_TYPE, default=None):
        return context.user_data.get('CHAT_STATE', default)

    @staticmethod
    def has(context: ContextTypes.DEFAULT_TYPE, name, state=None):
        ex_state = ChatState.get(context)

        if ex_state is None:
            return False

        if state is None:
            return str(ex_state).startswith(name)

        return (name + "|" + str(state)) == ex_state

    @staticmethod
    def unset(context: ContextTypes.DEFAULT_TYPE):
        return context.user_data.pop('CHAT_STATE') if 'CHAT_STATE' in context.user_data else False


@synchronize_function
async def get_user(app: Application, user_id):
    return await app.bot.getChat(user_id)


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def schedules_handler(app: Application):
    async def job_schedule_checker(context):
        schedules = DBSchedules.get_rows(
            {'timestamp': {'compare': '<', 'value': time.time()}}
        )

        c_time = time.time()

        for schedule in schedules:

            if schedule['timestamp'] > c_time:
                continue

            if '.' in schedule['handler']:
                class_name, method_name = schedule['handler'].rsplit('.', 1)

                if '.' in class_name:
                    class_obj = getattr(importlib.import_module(class_name), class_name.rsplit('.', 1)[1])
                else:
                    class_obj = globals()[class_name]

                caller = getattr(class_obj, method_name)
            else:
                caller = globals()[schedule['handler']]

            # Call the method dynamically
            caller(schedule, app)

    app.job_queue.run_repeating(
        job_schedule_checker,
        30,
        name="schedules_handler",
    )


def buildContext(app, update) -> CCT:
    """ Let's build telegram bot context on request
        Starting from app and current update
    """
    context = app.context_types.context.from_update(update, app)
    # await context.refresh_data()
    return context


def StateHandler(app: Application, state_name, callback: HandlerCallback[Update, CCT, RT], block=True):
    class _StateHandler(MessageHandler):

        def check_update(self, update: object) -> Optional[Union[bool, Dict[str, List[Any]]]]:
            if isinstance(update, Update):
                return self.filter_update(update) or False
            return None

        def filter_update(self, update: Update):
            if super().check_update(update):
                context = buildContext(app, update)

                return ChatState.has(context, state_name)
            return False

    return _StateHandler(filters.ALL, callback, block)


async def save_media(update: Update, context: ContextTypes.DEFAULT_TYPE, directory=None):
    message = update.message

    if message.photo:
        # If it's a photo, choose the last (highest resolution) one
        file_id = message.photo[-1].file_id
    elif message.video:
        # If it's a video, choose the video file
        file_id = message.video.file_id
    elif message.audio:
        # If it's an audio file, choose the audio file
        file_id = message.audio.file_id
    elif message.document:
        # If it's a document, choose the document file
        file_id = message.document.file_id
    else:
        return False

    file = await context.bot.getFile(file_id)

    if not directory:
        today = datetime.date.today()
        directory = f"{WMB_ABS_PATH}/data/feedback/{today.year}/{today.month}"

    directory.rstrip('/\\')

    # Generate a unique file name based on the file_id
    file_path = unique_file_name(directory, file.file.split('/')[-1])

    # Download the file to disk
    return await file.download_to_drive(custom_path=file_path)


def build_command_list(private: bool = False, group_name: str = None, admins: bool = False) -> List[Tuple[str, str]]:
    base_commands = [
        ("start", "Start or reset the bot"),
        ("home", "Return to home, quitting anything else."),
        ("random", "Return a random number 0,N if N is specified after the command"),
        ("alarm", "Add a new reminder (seconds from now | date + time) + text"),
        ("alarmslist", "Return a list of reminders set")
    ]

    return base_commands


async def post_shutdown(app: Application) -> None:
    Database.close()

    print("shutting down...")
    await app.shutdown()


async def post_init(app: Application) -> None:
    bot = app.bot

    Database.setup(f"{WMB_ABS_PATH}/data/database.db")

    await bot.set_my_commands(
        build_command_list(private=True),
        scope=BotCommandScopeAllPrivateChats(),
    )
    await bot.set_my_commands(
        build_command_list(private=False),
        scope=BotCommandScopeAllGroupChats(),
    )
