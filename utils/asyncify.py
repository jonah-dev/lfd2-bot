from concurrent.futures import ThreadPoolExecutor
from asyncio import wrap_future
from functools import wraps

def asyncify(fn):
    """
    We have some syncronous IO libraries (e.g. gsheets) and
    we want to be able to use async/await multitasking while
    they execute. This turns functions into async ones.
    """

    threads = ThreadPoolExecutor()
    @wraps(fn)
    def get_await_handle(*args, **kwargs):
        promise = threads.submit(fn, *args, **kwargs)
        return wrap_future(promise)

    return get_await_handle  