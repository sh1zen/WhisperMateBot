from enum import Enum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

from config import BOT_NAME
from workers.Database.DBMeta import DBMeta
from workers.Database.DBUsers import DBUsers
from workers.locale_handler import __


# enumeration to handle different keyboard types
class KeyboardType(Enum):
    HOME, ACTIONS, APPS, CANCEL, SHARE_LOCATION = range(5)
    SETTINGS_INLINE, ABOUT_INLINE, HELP_INLINE, LANGUAGES_INLINE, \
        GENDER_INLINE, CANCEL_ACCEPT_INLINE, CANCEL_INLINE, BACK_INLINE, YES_NO_INLINE = range(10, 19)


def getKeyboard(kType, user_id, prefix='', value=None, context=''):
    if not DBMeta.get_meta(user_id, 'keyboard', True):
        return None

    if kType == KeyboardType.HOME:
        keyboard = [
            [__('•Actions 🧮•', user_id), __('•Apps 🧩️•', user_id)],
            [__('•Settings ⚙️•', user_id), __('•About & Help ❓•', user_id)]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder=f"welcome to {BOT_NAME}")

    if kType == KeyboardType.CANCEL:
        keyboard = [['•Cancel•']]

        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if kType == KeyboardType.ACTIONS:
        keyboard = [
            [__('•Echo 🗣•', user_id), __('•CoinToss 🪙•', user_id)],
            [__('•Back•', user_id)]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if kType == KeyboardType.APPS:
        keyboard = [
            [__('•CryptoCoin 🪙•', user_id), __('•ChatIncognito 🫣•', user_id)],
            [__('•Back•', user_id)]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if kType == KeyboardType.SHARE_LOCATION:
        keyboard = [
            [KeyboardButton("Share Location", request_location=True)],
            [__('•Cancel•', user_id)]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if kType == KeyboardType.YES_NO_INLINE:
        keyboard = [
            [
                InlineKeyboardButton(
                    ("🔘 " if bool(value) else '') + __("Yes", user_id),
                    callback_data=f"{prefix}.{context}|1")
            ],
            [
                InlineKeyboardButton(
                    ("🔘 " if not bool(value) else '') + __("No", user_id),
                    callback_data=f"{prefix}.{context}|0")
            ],
            [
                InlineKeyboardButton(__("🔙 Back", user_id), callback_data=f"{prefix}.back")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    if kType == KeyboardType.BACK_INLINE:
        inline_keyboard = [[InlineKeyboardButton(__("🔙 Back", user_id), callback_data=f"{prefix}.back")]]
        return InlineKeyboardMarkup(inline_keyboard)

    if kType == KeyboardType.HELP_INLINE:
        keyboard = [
            [
                InlineKeyboardButton(__('Terms of services 📄', user_id), callback_data=f"{prefix}.tos"),
            ],
            [
                InlineKeyboardButton(__('Info 📖', user_id), callback_data=f"{prefix}.info"),
                InlineKeyboardButton(__('About 📖', user_id), callback_data=f"{prefix}.about"),
            ],
            [InlineKeyboardButton(__("Send Feedback 📬", user_id), callback_data=f"{prefix}.feedback")]
        ]

        return InlineKeyboardMarkup(keyboard)

    if kType == KeyboardType.CANCEL_ACCEPT_INLINE:
        keyboard = [
            [InlineKeyboardButton(__('Accept', user_id), callback_data=f"{prefix}.accept")],
            [InlineKeyboardButton(__('Cancel', user_id), callback_data=f"{prefix}.cancel")],
        ]

        return InlineKeyboardMarkup(keyboard)

    if kType == KeyboardType.CANCEL_INLINE:
        keyboard = [
            [InlineKeyboardButton(__('Cancel', user_id), callback_data=f"{prefix}.cancel")],
        ]

        return InlineKeyboardMarkup(keyboard)

    if kType == KeyboardType.GENDER_INLINE:

        if value is None:
            value = DBUsers.get_value(user_id, 'gender', 'none')

        keyboard = [
            [
                InlineKeyboardButton(
                    ("🔘" if value == 'male' else '') + __("👦 Male", user_id),
                    callback_data=f"{prefix}.set_gender|male")
            ],
            [
                InlineKeyboardButton(
                    ("🔘" if value == 'female' else '') + __("🧒 Female", user_id),
                    callback_data=f"{prefix}.set_gender|female")
            ],
            [
                InlineKeyboardButton(
                    ("🔘" if value == 'none' else '') + __("👤 None", user_id),
                    callback_data=f"{prefix}.set_gender|none")
            ],
            [
                InlineKeyboardButton(
                    __("🔙 Back", user_id),
                    callback_data=f"{prefix}.back")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    if kType == KeyboardType.SETTINGS_INLINE:
        keyboard = [
            [InlineKeyboardButton(__("🌐 Lang", user_id), callback_data=f"{prefix}.set_lang")],
            [InlineKeyboardButton(__("👦 Gender 🧒", user_id), callback_data=f"{prefix}.set_gender")],
            [InlineKeyboardButton(__("📄 Bio", user_id), callback_data=f"{prefix}.set_bio")],
            [InlineKeyboardButton(__("📆 Birthday", user_id), callback_data=f"{prefix}.set_birthday")],
            [InlineKeyboardButton(__("📍 Location", user_id), callback_data=f"{prefix}.set_location")],
            [InlineKeyboardButton(__("⚙️ Show", user_id), callback_data=f"{prefix}.dump")],
        ]

        return InlineKeyboardMarkup(keyboard)

    if kType == KeyboardType.LANGUAGES_INLINE:

        if value is None:
            value = DBUsers.get_value(user_id, 'lang', 'en')

        inline_keyboard = [
            [
                InlineKeyboardButton(("🔘" if value == 'en' else '') + "🇬🇧 En", callback_data=f"{prefix}.set_lang|en"),
                InlineKeyboardButton(("🔘" if value == 'fr' else '') + "🇫🇷 Fr", callback_data=f"{prefix}.set_lang|fr"),
                InlineKeyboardButton(("🔘" if value == 'it' else '') + "🇮🇹 It", callback_data=f"{prefix}.set_lang|it")
            ],
            [
                InlineKeyboardButton(("🔘" if value == 'es' else '') + "🇪🇸 Es", callback_data=f"{prefix}.set_lang|es"),
                InlineKeyboardButton(("🔘" if value == 'de' else '') + "🇩🇪 De", callback_data=f"{prefix}.set_lang|de"),
            ],
            [
                InlineKeyboardButton(__("🔙 Back", user_id), callback_data=f"{prefix}.back")
            ]
        ]

        return InlineKeyboardMarkup(inline_keyboard)

    if kType == KeyboardType.ABOUT_INLINE:
        inline_keyboard = [
            [
                InlineKeyboardButton(text="GitHub", url='https://github.com/sh1zen'),
            ],
            [
                InlineKeyboardButton(__("🔙 Back", user_id), callback_data=f"{prefix}.back")
            ]
        ]

        return InlineKeyboardMarkup(inline_keyboard)
