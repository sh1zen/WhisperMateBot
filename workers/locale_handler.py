import builtins
import gettext

from workers.Database.DBUsers import DBUsers


class Localizer:

    def install(self):
        builtins.__dict__['__'] = self.translate
        builtins.__dict__['_all'] = self.translate_all

    @staticmethod
    def translate(text, user_id, *args):
        lang_cache = {}

        lang = DBUsers.get_value(user_id, 'lang', 'en')

        if lang not in lang_cache:
            try:
                lang_cache[lang] = gettext.translation("wmb", localedir="../locales/", languages=[lang])
            except Exception:
                lang_cache[lang] = None

        translated_text = lang_cache.get(lang).gettext(text) if lang_cache.get(lang) is not None else text

        if args:
            return translated_text.format(*args)
        else:
            return translated_text

    @staticmethod
    def translate_all(text):
        return [text]


def __(text, user_id, *args):
    return Localizer.translate(text, user_id, *args)


def _all(text):
    return Localizer.translate_all(text)
