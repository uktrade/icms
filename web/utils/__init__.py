import time
from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def time_snippet(msg: str) -> Generator[None, None, None]:
    print(f"Timing this: {msg}")
    start = time.perf_counter()

    yield

    end = time.perf_counter()
    duration = end - start

    print(f"Time taken: {duration} seconds")
