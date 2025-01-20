import time


class Timer:
    def __init__(self):
        self.start: float | None = None

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type, value, traceback):
        if isinstance(self.start, float):
            print(f"Elapsed time: {time.time() - self.start:.2f}")
