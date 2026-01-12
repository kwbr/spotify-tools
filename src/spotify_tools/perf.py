"""
Performance measurement utilities for Spotify tools.
"""

import contextlib
import functools
import time
from contextlib import contextmanager


class TimingResult:
    """Container for timing result data."""

    def __init__(self, name, elapsed):
        self.name = name
        self.elapsed = elapsed
        self.ms = elapsed * 1000  # convert to milliseconds

    def __str__(self):
        return f"{self.name}: {self.ms:.2f}ms"


@contextlib.contextmanager
def measure_time(name="Operation"):
    """
    Context manager to measure execution time.

    Args:
        name: Name of the operation being timed.

    Returns:
        TimingResult with elapsed time in seconds.
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        result = TimingResult(name, elapsed)
        print(f"TIMING: {result}")


@contextmanager
def silent_timer(name="Operation"):
    """
    A no-op context manager for when timing is disabled.

    Args:
        name: Name of the operation (ignored).
    """
    try:
        yield
    finally:
        pass


def timed(func):
    """
    Decorator to measure function execution time.

    Args:
        func: Function to be timed.

    Returns:
        Wrapped function that prints timing information.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start_time
            result = TimingResult(func.__name__, elapsed)
            print(f"TIMING: {result}")

    return wrapper
