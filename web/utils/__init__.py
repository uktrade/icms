import time
from contextlib import contextmanager


@contextmanager
def time_snippet(msg):
    print(f"Timing this: {msg}")
    start = time.perf_counter()

    yield

    end = time.perf_counter()
    duration = end - start

    print(f"Time taken: {duration} seconds")
