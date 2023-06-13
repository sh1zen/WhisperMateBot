import asyncio
import functools
import hashlib
import importlib
import os
import pickle
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from workers.constants import WMB_ABS_PATH


def md5(string):
    # Create an instance of the MD5 hash object
    md5_hash = hashlib.md5()

    # Convert the string to bytes and update the hash object
    md5_hash.update(string.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    return md5_hash.hexdigest()


def parse_time(time_sec, interval=True) -> int:
    time_sec = time_sec.strip()

    if time_sec.isnumeric():
        return int(time_sec) if interval else time.time() + int(time_sec)

    if re.match(r'^(\d{2}:)\d{2}:\d{1,2}?$', time_sec):
        time_sec = f'{datetime.now().strftime("%Y-%m-%d")} {time_sec}'

    possible_formats = ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%m-%d %H:%M', '%m-%d %H:%M:%S']

    timestamp = None
    for format_string in possible_formats:
        try:
            timestamp = datetime.strptime(time_sec, format_string).timestamp()
            break
        except ValueError:
            pass

    if not interval and timestamp:
        return int(timestamp)

    c_timestamp = time.time()

    if timestamp:
        ltime = int(timestamp - c_timestamp)
        return ltime if ltime > 0 else 0

    return 0


def slugify(string):
    # Convert to lowercase
    string = string.lower()

    # Remove special characters and replace spaces with hyphens
    string = re.sub(r"[^\w\s-]", "", string)
    string = re.sub(r"\s+", "-", string)

    return string


def unique_file_name(directory, filename=None):
    if not filename:
        filename = time.time()

    full_path = os.path.join(directory, filename)
    prefix, extension = os.path.splitext(filename)

    iterator = 1
    while os.path.exists(full_path):
        filename = f"{prefix}-{iterator}.{extension}"
        full_path = os.path.join(directory, filename)
        if not os.path.exists(full_path):
            break
        iterator += 1

    return full_path


def auto_loader(path):
    modules = []

    # Get a list of all files in the folder
    files = os.listdir(path)

    wrapper_path = os.path.relpath(path, WMB_ABS_PATH).replace('\\', '.').replace('/', '.') + '.'

    # Iterate over the files
    for file_name in files:

        file_path = os.path.join(path, file_name)

        if os.path.isdir(file_path):
            modules.extend(auto_loader(file_path))

        elif file_name.endswith('.py'):
            # Remove the file extension
            module_name = os.path.splitext(file_name)[0]

            # Import the module dynamically
            module = importlib.import_module(wrapper_path + module_name)

            modules.append(module)

    return modules


def limited_list(queue, item, max_len=1000):
    while len(queue) > max_len:
        queue.pop(0)

    return queue.append(item)


def maybe_serialize(data):
    if isinstance(data, (list, dict, set)):
        return pickle.dumps(data)
    return data


def maybe_unserialize(data):
    if not data:
        return data

    try:
        return pickle.loads(data)
    except (pickle.UnpicklingError, AttributeError, TypeError):
        return data


def unpacked_s(text, selector=False, delimiter='|'):
    splitted = text.split(delimiter) if delimiter in text else ''

    if selector:
        return splitted[selector] if selector < len(splitted) else None

    return splitted


def parse_date_format(date_str, d_format='%Y-%m-%d'):
    date_str = str(date_str).strip()

    try:
        datetime.strptime(date_str, d_format)
        return date_str
    except ValueError:
        return False


def get_flag_emoji(country_code):
    if country_code == 'en':
        country_code = 'gb'

    code_points = [127397 + ord(char) for char in country_code.upper()]
    return ''.join(chr(code_point) for code_point in code_points)


def calculate_shift(seconds, date_from=None, as_timestamp=False):
    if date_from is None:
        date_from = datetime.now().timestamp()
    elif isinstance(date_from, str):
        date_from = datetime.strptime(date_from, "%Y-%m-%d").timestamp()
    elif isinstance(date_from, datetime):
        date_from = datetime.timestamp()

    # Calculate time shift
    new_date = int(date_from) + seconds

    return new_date if as_timestamp else datetime.fromtimestamp(new_date).strftime("%Y-%m-%d")


def synchronize_function(fn):
    """ turn an async function to sync function """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        res = fn(*args, **kwargs)
        if asyncio.iscoroutine(res):
            return asyncio.get_event_loop().run_until_complete(res)
        return res

    return wrapper


def asynchronize_function(fn):
    """ turns a sync function to async function using threads """

    pool = ThreadPoolExecutor()

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        future = pool.submit(fn, *args, **kwargs)
        return asyncio.wrap_future(future)

    return wrapper
