from datetime import datetime

from telegram import Update
from telegram.ext import (ContextTypes)

from utils.ModuleBase import ModuleBase
from utils.keyboards import KeyboardType, getKeyboard
from utils.utility import unpacked_s, parse_date_format, get_flag_emoji
from workers.Database.DBUsers import DBUsers
from workers.locale_handler import __

STATE_WAIT_BIO, STATE_WAIT_BIRTHDAY, STATE_WAIT_LOCATION = range(3)


class Settings(ModuleBase):
    priority = 2

    async def handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id

        await update.message.reply_text(
            __("<b>Set your options here:</b>", user_id),
            reply_markup=getKeyboard(KeyboardType.SETTINGS_INLINE, user_id, self.hook)
        )
        self.unset_state(context)

    async def stateHandler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id
        request = update.message.text or ''

        # handle cancel
        if self.commandRegex('cancel').match(request):
            self.unset_state(context)
            await update.message.reply_text(
                "👍",
                reply_markup=getKeyboard(KeyboardType.HOME, user_id)
            )
            return

        if self.has_state(context, STATE_WAIT_BIRTHDAY):
            parsed = parse_date_format(update.message.text)

            if not parsed:
                await update.message.reply_text(
                    __("<b>The date sent is not valid, must be YYYY-MM-DD\nTry again:</b>", user_id),
                )
                return

            DBUsers.update_value(user_id, 'birthday', parsed)

        elif self.has_state(context, STATE_WAIT_BIO):
            parsed = str(update.message.text).strip()

            if not parsed or len(parsed) > 140:
                await update.message.reply_text(
                    __("<b>The bio you sent is not valid: {}\nTry again:</b>", user_id, update.message.text),
                )
                return

            DBUsers.update_value(user_id, 'bio', parsed)

        elif self.has_state(context, STATE_WAIT_LOCATION):
            location = update.message.location

            if not location:
                await update.message.reply_text(
                    __("<b>Is not a location\nTry again:</b>", user_id),
                )
                return

            DBUsers.update_value(
                user_id,
                'location',
                {
                    'lat': location.latitude,
                    'long': location.longitude,
                    'accuracy': location.horizontal_accuracy
                }
            )

        await update.message.reply_text("👍", reply_markup=getKeyboard(KeyboardType.HOME, user_id))
        self.unset_state(context)

    async def callbackQueryHandler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        query_data = query.data

        user_id = update.effective_user.id

        if self.checkCallback(query_data, 'back'):

            await query.edit_message_text(
                __('<b>Set your options here:</b>', user_id),
                reply_markup=getKeyboard(KeyboardType.SETTINGS_INLINE, user_id, self.hook)
            )
            self.unset_state(context)

        elif self.checkCallback(query_data, 'dump'):

            user = DBUsers.get_row(user_id)

            facts = {
                __("lang", user_id): get_flag_emoji(user['lang']),
                __("gender", user_id): user['gender'],
                __("bio", user_id): user['bio'],
                __("birthday", user_id): user['birthday'],
                __("age", user_id): (datetime.today() - datetime.strptime(user['birthday'], "%Y-%m-%d")).days // 365,
                __("location", user_id): user['location'],
                __("bot", user_id): 'yes' if bool(user['is_bot']) else 'no',
                __("reported", user_id): 'yes' if bool(user['reported']) else 'no',
            }

            if len(facts) == 0:
                await query.message.reply_text(__("<b>No data set.</b>", user_id))
            else:
                await query.message.reply_text(
                    "\n".join([f"{key}: <b><i>{value}</i></b>" for key, value in facts.items() if value]))

        else:
            settings = {
                'set_lang': {
                    'message': __('Please select a language:', user_id),
                    'keyboard': KeyboardType.LANGUAGES_INLINE
                },
                'set_gender': {
                    'message': __('Set your gender here:', user_id),
                    'keyboard': KeyboardType.GENDER_INLINE
                },
                'set_bio': {
                    'message': __("<b>Send your bio (max 140 chars):</b>", user_id),
                    'keyboard': KeyboardType.CANCEL,
                    'state': STATE_WAIT_BIO,
                },
                'set_birthday': {
                    'message': __(
                        "<b>Send your birthday in the following format YYYY-MM-DD (ex. 2000-02-23):</b>", user_id),
                    'keyboard': KeyboardType.CANCEL,
                    'state': STATE_WAIT_BIRTHDAY,
                },
                'set_location': {
                    'message': __("<b>Send now your location</b>\n\n" +
                                  "<i>Please do it while you are not in a chat, so there are no risks it can be sent to an user.</i>",
                                  user_id),
                    'keyboard': KeyboardType.SHARE_LOCATION,
                    'state': STATE_WAIT_LOCATION,
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
                                "<b>Updating {}, to cancel this operation press Cancel button.</b>\n\n" +
                                "<i>Please do it while you are not in a chat, so there are no risks it can be sent to an user.</i>",
                                user_id,
                                key[len('set_'):]
                            ),
                            reply_markup=getKeyboard(value.get('keyboard'), user_id, self.hook)
                        )

                        self.set_state(context, value.get('state'))
                    else:
                        new_value = unpacked_s(query_data, 1)

                        if new_value:
                            DBUsers.update_value(user_id, key[len('set_'):], new_value)
                            await query.answer('👍')

                        await query.edit_message_text(
                            value.get('message'),
                            reply_markup=getKeyboard(
                                value.get('keyboard'), user_id, self.hook) if value.get('keyboard') else None
                        )
