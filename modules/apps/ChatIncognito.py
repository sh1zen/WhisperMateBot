from datetime import datetime
from enum import Enum

import telegram
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, \
    CommandHandler

from utils.ModuleBase import ModuleBase
from utils.keyboards import getKeyboard, KeyboardType
from utils.utility import unpacked_s, limited_list, calculate_shift, maybe_unserialize
from workers.Database.DBChat import DBChat
from workers.Database.DBMeta import DBMeta
from workers.Database.DBUsers import DBUsers
from workers.Database.Database import Database
from workers.accessibility import send_typing_action
from workers.bot import StateHandler
from workers.constants import YEAR_IN_SECONDS
from workers.locale_handler import __


class ChatIncognito(ModuleBase):
    priority = 0

    CHAT_MODE, CHAT_IDLE = range(2)
    STATE_WAIT_AGE, STATE_WAIT_DISTANCE = range(2)
    CSTATE_OFFLINE, CSTATE_CHATTING, CSTATE_WAITING = range(3)

    class KeyboardType(Enum):
        SETTINGS, HOME, CHATTING, STOP_SEARCHING = range(4)

    def register_handlers(self, keyboard=None):
        conv_handler = ConversationHandler(
            entry_points=[
                MessageHandler(self.keyBoardCommandFilter('ChatIncognito'), self.handler)
            ],
            states={
                self.CHAT_MODE: [
                    MessageHandler(filters.Regex(r'^/reset$'), self.handler),
                    CommandHandler('report', self.report),
                    MessageHandler(filters.ALL, self.chat)
                ],
                self.CHAT_IDLE: [
                    MessageHandler(filters.Regex(r'^/reset$'), self.handler),
                    StateHandler(self.app, self.hook, self.stateHandler),
                    CommandHandler('report', self.report),
                    MessageHandler(filters.TEXT, self.commands_handler),
                    CallbackQueryHandler(self.callbackQueryHandler)
                ],
            },
            fallbacks=[MessageHandler(filters.ALL, self.handler)],
            name='ChatIncognito',
            allow_reentry=True,
            persistent=True
        )

        self.app.add_handler(conv_handler)

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        # unset any states if there is leftover
        self.unset_state(context)
        user_id = update.effective_user.id

        # save current chat id if not exist
        if not DBChat.has({'user_id': user_id}):
            DBChat.insert({'user_id': user_id, 'chat_id': update.effective_chat.id})

        await update.message.reply_text(
            __(
                "<b>Welcome to ChatIncognito</b>\n\n" +
                "<i>please follow the rules and not spam.</i>",
                user_id
            ),
            reply_markup=self.keyboards(self.KeyboardType.HOME, user_id)
        )
        return self.CHAT_IDLE

    async def callbackQueryHandler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        query_data = query.data
        user_id = update.effective_user.id

        if self.checkCallback(query_data, 'back'):
            await query.edit_message_text(
                __('<b>Set your partners options here:</b>', user_id),
                reply_markup=self.keyboards(self.KeyboardType.SETTINGS, user_id)
            )
        else:

            settings = {
                'set_gender': {
                    'message': __('<b>Who do you want to chat with? Set none for any type.</b>', user_id),
                    'keyboard': KeyboardType.GENDER_INLINE
                },
                'set_media_enabled': {
                    'message': __('<b>Do you want to allow other users to send photo or video to you?</b>:', user_id),
                    'keyboard': KeyboardType.YES_NO_INLINE
                },
                'set_reopen': {
                    'message': __(
                        "<b>Do you want other users you chat with, to send you requests to open a chat again after 5 minutes it has been closed?</b>",
                        user_id),
                    'keyboard': KeyboardType.YES_NO_INLINE
                },
                'set_age_range': {
                    'message': __("<b>Send partner age range like '20-25':</b>", user_id),
                    'state': self.STATE_WAIT_AGE,
                },
                'set_distance': {
                    'message': __(
                        "<b>Send partner distance range in Km, like 20, send 0 to not consider distance.</b>\n\n",
                        user_id),
                    'state': self.STATE_WAIT_DISTANCE,
                }
            }

            for key, value in settings.items():
                if self.checkCallback(query_data, key, True):

                    if value.get('state') is not None:
                        await query.edit_message_text(
                            value.get('message'),
                            reply_markup=getKeyboard(KeyboardType.BACK_INLINE, user_id, self.hook)
                        )

                        await query.message.reply_text(
                            __(
                                "<i>Updating {}, to cancel this operation press Cancel button.</i>",
                                user_id,
                                key[len('set_'):]
                            ),
                            reply_markup=getKeyboard(KeyboardType.CANCEL, user_id)
                        )

                        self.set_state(context, value.get('state'))
                    else:
                        new_value = unpacked_s(query_data, 1)

                        if new_value:
                            DBChat.update_value(user_id, key[len('set_'):], new_value)
                            await query.answer('👍')

                        await query.edit_message_text(
                            value.get('message'),
                            reply_markup=getKeyboard(
                                value.get('keyboard'),
                                user_id,
                                prefix=self.hook,
                                value=DBChat.get_value({'user_id': user_id}, key[len('set_'):]),
                                context=key
                            ) if value.get('keyboard') else None
                        )

        return self.CHAT_IDLE

    async def stateHandler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id

        parsed = str(update.message.text).strip()

        # handle cancel
        if self.commandRegex('cancel').match(parsed):
            await update.message.reply_text(
                "👍",
                reply_markup=self.keyboards(self.KeyboardType.HOME, user_id)
            )
            self.unset_state(context)
        elif self.has_state(context, self.STATE_WAIT_AGE):

            if '-' not in parsed:
                await update.message.reply_text(
                    __("<b>The age range you sent is not valid: {}\nTry again:</b>", user_id, parsed),
                )
            else:
                min_age, max_age = [int(value) for value in parsed.split('-')]

                if min_age > max_age:
                    min_age, max_age = max_age, min_age

                if min_age < 0 or min_age >= 99 or max_age < 1 or max_age > 100:
                    await update.message.reply_text(
                        __("<b>The age range you sent is not valid, range 0-100\nTry again:</b>", user_id),
                    )
                else:
                    DBChat.update_value(user_id, 'min_age', min_age)
                    DBChat.update_value(user_id, 'max_age', max_age)
                    await update.message.reply_text(
                        "👍",
                        reply_markup=self.keyboards(self.KeyboardType.HOME, user_id)
                    )
                    self.unset_state(context)

        elif self.has_state(context, self.STATE_WAIT_DISTANCE):

            if not parsed.isnumeric():
                await update.message.reply_text(
                    __("<b>The distance range you sent is not valid: {}\nTry again:</b>", user_id, parsed),
                )
            else:
                DBChat.update_value(user_id, 'distance', parsed)
                await update.message.reply_text(
                    "👍",
                    reply_markup=self.keyboards(self.KeyboardType.HOME, user_id)
                )
                self.unset_state(context)

        return self.CHAT_IDLE

    async def commands_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        request = update.message.text or ''
        user_id = update.effective_user.id

        if self.commandRegex('new chat').match(request):
            await self.handle_chat_search(update, context)
            return self.CHAT_MODE

        elif self.commandRegex('Restore chat').match(request):
            if len(DBMeta.get_meta(user_id, 'prev_mates', [])) > 0:
                await update.message.reply_text(
                    __("<b>Tap on the chat you want to reopen:</b>", user_id),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    DBUsers.get_value(user_id, 'first_name', __('user', user_id)),
                                    callback_data=f"{self.hook}.reopen.{mate_id}")
                            ] for mate_id in DBMeta.get_meta(user_id, 'prev_mates', [])]
                    )
                )
            else:
                await update.message.reply_text(
                    __("<b>No chat to reopen.</b>", user_id),
                    reply_markup=self.keyboards(self.KeyboardType.HOME, user_id)
                )

        elif self.commandRegex('exit').match(request):
            await update.message.reply_text(
                __("<b>Quit ChatIncognito</b>", user_id),
                reply_markup=getKeyboard(KeyboardType.APPS, user_id)
            )
            return ConversationHandler.END

        elif self.commandRegex('cancel').match(request):
            await update.message.reply_text(
                __("👍", user_id),
                reply_markup=self.keyboards(self.KeyboardType.HOME, user_id)
            )

        elif self.commandRegex('settings').match(request):
            await update.message.reply_text(
                __("<b>Set your partners options here:</b>", user_id),
                reply_markup=self.keyboards(self.KeyboardType.SETTINGS, user_id)
            )

        return self.CHAT_IDLE

    async def report(self):
        # todo implement
        pass

    @send_typing_action
    async def chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

        user_id = update.effective_user.id
        message_text = update.message.text or ''

        new_chat_state = self.CHAT_MODE

        if DBChat.get_value({'user_id': user_id}, 'status', self.CSTATE_OFFLINE) == self.CSTATE_OFFLINE:

            # handle if the mate left the chat, and we are still in CHAT_MODE (ConversationHandler)
            # keyboard has already been updated by self.handle_chat_left
            new_chat_state = await self.commands_handler(update, context)

        elif self.commandRegex('Stop Searching').match(message_text):
            await update.message.reply_text(
                __(
                    "<b>Now, you are not searching anymore for users.</b>",
                    user_id,
                ),
                reply_markup=self.keyboards(self.KeyboardType.HOME, user_id)
            )
            self.handle_chat_left(update)
            new_chat_state = self.CHAT_IDLE

        elif self.commandRegex('Leave Chat').match(message_text):
            await update.message.reply_text(
                __(
                    "<b>⬆️CHAT OVER⬆️</b>\n\n" +
                    "You left the chat.",
                    user_id,
                ),
                reply_markup=self.keyboards(self.KeyboardType.HOME, user_id)
            )
            self.handle_chat_left(update)
            new_chat_state = self.CHAT_IDLE

        elif self.commandRegex('New Chat').match(message_text) or self.commandRegex('Another User').match(message_text):
            await update.message.reply_text(
                __(
                    "<b>⬆️CHAT OVER⬆️</b>\n\n" +
                    "You left the chat.\n\n" +
                    "<b>Waiting for someone...🔍</b>",
                    user_id,
                ),
                reply_markup=self.keyboards(self.KeyboardType.STOP_SEARCHING, user_id)
            )
            self.handle_chat_left(update, waiting=True)
        else:
            await self.handle_chat(update, context)

        return new_chat_state

    async def handle_chat_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id

        user = DBUsers.get_row(user_id)

        if bool(user['is_bot']) or bool(user['reported']):
            await update.message.reply_text(
                __("<b>It seems you were reported or you are a bot, unable to start a new conversation.</b>", user_id),
                reply_markup=self.keyboards(self.KeyboardType.HOME, user_id)
            )
            return self.CHAT_IDLE

        chat_preferences = DBChat.get_row({'user_id': user_id})

        if not chat_preferences:
            return self.CHAT_IDLE

        min_age, max_age = (int(chat_preferences['min_age']) or 0, int(chat_preferences['max_age']) or 100)

        user_age = (datetime.today() - datetime.strptime(user['birthday'], "%Y-%m-%d")).days // 365

        query = {
            'action': 'SELECT',
            'fields': '*',
            'from': {
                DBUsers.tableName: 't1',
                DBChat.tableName: 't2',
            },
            'where': {
                't1.user_id': {
                    'value': 't2.user_id',
                    'raw': True
                },
                't1.is_bot': '0',
                't1.reported': '0',
                't1.lang': user['lang'],
                't1.gender': chat_preferences['gender'] if chat_preferences['gender'] != 'none' else None,
                't1.birthday': {
                    'compare': 'BETWEEN',
                    'value': [
                        calculate_shift(-max_age * YEAR_IN_SECONDS),
                        calculate_shift(-min_age * YEAR_IN_SECONDS)
                    ] if min_age != 0 or max_age != 100 else None
                },
                't2.status': self.CSTATE_WAITING,
                't2.gender': {
                    'compare': 'IN',
                    'value': ['none', user['gender']]
                },
                't2.min_age': {
                    'compare': '<=',
                    'value': user_age
                },
                't2.max_age': {
                    'compare': '>=',
                    'value': user_age
                }
            },
            'orderby': 't2.id DESC'
        }

        matched = Database.get_rows(query)

        total_matched = len(matched)

        if total_matched == 0:
            DBChat.update_value(user_id, 'status', self.CSTATE_WAITING)
            await update.message.reply_text(
                __("<b>Waiting for someone...🔍</b>", user_id),
                reply_markup=self.keyboards(self.KeyboardType.STOP_SEARCHING, user_id)
            )
        else:
            chatting_with = {}

            max_distance = int(chat_preferences['distance'] or 0)
            loc_data = maybe_unserialize(user['location'])

            if max_distance > 0 and bool(loc_data):
                from haversine import haversine, Unit

                loc_user_tuple = (loc_data['lat'], loc_data['long'])

                for may_match in matched:

                    mm_loc_data = maybe_unserialize(may_match['location'])

                    if not mm_loc_data:
                        continue

                    mm_loc_tuple = (mm_loc_data['lat'], mm_loc_data['long'])

                    distance = haversine(loc_user_tuple, mm_loc_tuple, unit=Unit.METERS)

                    if distance > max_distance:
                        continue

                    if not int(may_match['distance'] or 0) or distance <= int(may_match['distance']):
                        chatting_with = may_match
                        break
            else:
                chatting_with = matched[0]

            if bool(chatting_with):

                chatting_with_id = chatting_with['id']
                DBChat.update_value(user_id, 'status', self.CSTATE_CHATTING)
                DBChat.update_value(chatting_with_id, 'status', self.CSTATE_CHATTING)

                gender = {
                    'male': '👦',
                    'female': '🧒',
                }

                await context.bot.send_message(
                    chat_id=chatting_with_id,
                    text=__(
                        "<b>Found a match</b>\n\n" +
                        f"{gender[user['gender']] or '👤'} <b>{user_age}</b>" +
                        f"<i>{user['bio']}</i>",
                        chatting_with_id
                    ),
                    reply_markup=self.keyboards(self.KeyboardType.CHATTING, chatting_with_id)
                )

                match_age = (datetime.today() - datetime.strptime(user['birthday'], "%Y-%m-%d")).days // 365

                await update.message.reply_text(
                    __(
                        "<b>Found a match</b>\n\n" +
                        f"{gender[chatting_with['gender']] or '👤'} <b>{match_age}</b>" +
                        f"<i>{chatting_with['bio']}</i>",
                        user_id
                    ),
                    reply_markup=self.keyboards(self.KeyboardType.CHATTING, user_id)
                )
            else:

                DBChat.update_value(user_id, 'status', self.CSTATE_WAITING)
                await update.message.reply_text(
                    __(
                        "<b>No user found in your area, with distance ({}km) set.</b>\n" +
                        "<i>{} users found more distant with your criteria.</i>\n\n" +
                        "<b>Waiting for someone...🔍</b>",
                        user_id,
                        max_distance,
                        total_matched
                    ),
                    reply_markup=self.keyboards(self.KeyboardType.STOP_SEARCHING, user_id)
                )

    def handle_chat_left(self, update: Update, waiting=False):

        user_id = update.effective_user.id

        chatting_with_id = DBMeta.get_meta(user_id, 'chat_mate', 0)

        DBMeta.set_meta(user_id, 'chat_mate', 0)
        DBChat.update_value(user_id, 'status', self.CSTATE_WAITING if waiting else self.CSTATE_OFFLINE)

        if chatting_with_id:
            # reset mate chatting with
            DBMeta.set_meta(chatting_with_id, 'chat_mate', 0)
            DBChat.update_value(chatting_with_id, 'status', self.CSTATE_OFFLINE)

            update.message.reply_text(
                __(
                    "<b>⬆️CHAT OVER⬆️</b>\n\n" +
                    "Your partner left the chat.",
                    chatting_with_id,
                ),
                reply_markup=self.keyboards(self.KeyboardType.HOME, chatting_with_id)
            )

            # save the user we are chatting with, prev_mates
            DBMeta.set_meta(
                user_id,
                'prev_mates',
                limited_list(DBMeta.get_meta(user_id, 'prev_mates'), chatting_with_id, 5)
            )
            # save us to the user we are chatting with, prev_mates
            DBMeta.set_meta(
                chatting_with_id,
                'prev_mates',
                limited_list(DBMeta.get_meta(chatting_with_id, 'prev_mates'), user_id, 5)
            )

    @send_typing_action
    async def handle_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        # Get the received message
        message = update.message
        user_id = update.effective_user.id

        chatting_with_id = DBMeta.get_meta(user_id, 'chat_mate', 0)

        if not chatting_with_id:
            await update.message.reply_text(__("Something went wrong.", user_id))
            return self.CHAT_MODE

        try:
            # Forward different types of messages to the destination chat
            if message.photo:
                photo = message.photo[-1]  # Get the largest available photo
                if DBChat.get_value({'user_id': chatting_with_id}, 'media_enabled', True):
                    await context.bot.send_photo(chat_id=chatting_with_id, photo=photo.file_id, caption=message.caption)
                else:
                    await update.message.reply_text(
                        __("<b>The user you are chatting with doesn't want to receive photo or video.</b>", user_id)
                    )
            elif message.audio:
                await context.bot.send_audio(chat_id=chatting_with_id, audio=message.audio.file_id,
                                             caption=message.caption)
            elif message.video:
                if DBChat.get_value({'user_id': chatting_with_id}, 'media_enabled', True):
                    await context.bot.send_video(chat_id=chatting_with_id, video=message.video.file_id,
                                                 caption=message.caption)
                else:
                    await update.message.reply_text(
                        __("<b>The user you are chatting with doesn't want to receive photo or video.</b>", user_id)
                    )
            elif message.text:
                await context.bot.send_message(chat_id=chatting_with_id, text=message.text)
            elif message.document:
                await context.bot.send_document(chat_id=chatting_with_id, document=message.document.file_id,
                                                caption=message.caption)
            elif message.voice:
                await context.bot.send_voice(chat_id=chatting_with_id, voice=message.voice.file_id,
                                             caption=message.caption)
            elif message.sticker:
                await context.bot.send_sticker(chat_id=chatting_with_id, sticker=message.sticker.file_id)
            elif message.contact:
                await context.bot.send_sticker(chat_id=chatting_with_id, contact=message.contact)
            else:
                await update.message.reply_text(__("This content type forward is not yet supported.", user_id))

        except telegram.error.TelegramError as e:
            print(f"Error forwarding message: {e}")

        return self.CHAT_MODE

    def keyboards(self, kType, user_id):

        if kType == self.KeyboardType.HOME:
            return ReplyKeyboardMarkup(
                [
                    [__('•New Chat ✅•', user_id), __('•Restore chat 🔄•', user_id), __('•Settings ⚙️•', user_id)],
                    [__('•Exit 🚫•', user_id)]
                ],
                resize_keyboard=True
            )

        if kType == self.KeyboardType.STOP_SEARCHING:
            return ReplyKeyboardMarkup(
                [
                    [__('•Stop searching 🔍•', user_id)]
                ],
                resize_keyboard=True
            )

        if kType == self.KeyboardType.CHATTING:
            return ReplyKeyboardMarkup(
                [
                    [__('•Leave Chat ❌•', user_id), __('•Another User 🔄•', user_id)]
                ],
                resize_keyboard=True
            )

        if kType == self.KeyboardType.SETTINGS:
            keyboard = [
                [InlineKeyboardButton(__("👦 Partner Gender 🧒", user_id), callback_data=f"{self.hook}.set_gender")],
                [
                    InlineKeyboardButton(
                        __(
                            "📆 Partner Age ({}-{})",
                            user_id,
                            DBChat.get_value({'user_id': user_id}, 'min_age', 0),
                            DBChat.get_value({'user_id': user_id}, 'max_age', 100)
                        ),
                        callback_data=f"{self.hook}.set_age_range"
                    )
                ],
                [
                    InlineKeyboardButton(
                        __("📍 Distance range {} km", user_id, DBChat.get_value({'user_id': user_id}, 'distance', '')),
                        callback_data=f"{self.hook}.set_distance"
                    )
                ],
                [InlineKeyboardButton(__("🔄 Allow reopen chat requests", user_id),
                                      callback_data=f"{self.hook}.set_reopen")],
                [InlineKeyboardButton(__("📷 Allow photo/video", user_id),
                                      callback_data=f"{self.hook}.set_media_enabled")],
            ]
            return InlineKeyboardMarkup(keyboard)
