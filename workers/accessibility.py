import binascii
import os
from functools import wraps

from Crypto.Cipher import AES
from Crypto.Hash import SHA3_512
from Crypto.Util.Padding import pad, unpad
from telegram.constants import ChatAction


def decrypt(file):
    if not os.path.exists(file):
        return []

    fr = open(file, 'r')
    hashed_key = binascii.a2b_base64(fr.readline().encode())
    wmb_key = os.environ['WMB_CIPHER_KEY']

    if len(wmb_key) < 16:
        key = pad(wmb_key.encode(), 16)
    elif len(wmb_key) > 16:
        key = wmb_key[:16].encode()
    else:
        key = wmb_key.encode()

    hk = SHA3_512.new(key).digest()

    if hk != hashed_key:
        print('Wrong key!')
        return []

    aes = AES.new(key, AES.MODE_ECB)

    res = []

    for i in fr:
        res.append(int(unpad(aes.decrypt(binascii.a2b_base64(i.encode())), 16).decode().strip()))

    fr.close()

    return res


# Handling of restricted commands
LIST_OF_ADMINS = decrypt("admins.txt")


def restricted(func):
    """Enable restricted content only to admins"""

    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in LIST_OF_ADMINS:
            update.message.reply_text(
                "Unauthorized access denied for {}. This action will be reported.".format(user_id))
            return
        return func(update, context, *args, **kwargs)

    return wrapped


def send_action(action):
    """Sends 'action' while processing func command"""

    def decorator(func):
        @wraps(func)  # Preserve the original function's name and docstring
        async def wrapper(*args, **kwargs):

            if args and isinstance(args[0], object) and hasattr(args[0], func.__name__):
                pos = 1
            else:
                pos = 0

            # context, update
            await args[pos + 1].bot.send_chat_action(chat_id=args[pos].effective_message.chat_id, action=action)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# The message "is typing" appears while the bot is processing messages
send_typing_action = send_action(ChatAction.TYPING)
