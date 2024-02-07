import time


class Timer:
    def __init__(self):
        self.start = None

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, type, value, traceback):
        print(f"Elapsed time: {time.time() - self.start:.2f}")
