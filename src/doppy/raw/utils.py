from io import SEEK_END, BufferedIOBase
from pathlib import Path


def bytes_from_src(src: str | bytes | Path | BufferedIOBase) -> bytes:
    if isinstance(src, (str, Path)):
        with open(src, "rb") as f:
            return f.read()
    elif isinstance(src, bytes):
        return src
    elif isinstance(src, BufferedIOBase):
        return src.read()
    else:
        raise TypeError(f"Unexpected type {type(src)} for src")


def size_of_src(src: str | bytes | Path | BufferedIOBase) -> int | None:
    """Size in bytes without reading the source, None if it cannot be told.

    Measuring by reading would allocate the memory the guard exists to protect.
    """
    if isinstance(src, (str, Path)):
        return Path(src).stat().st_size
    if isinstance(src, bytes):
        return len(src)
    if isinstance(src, BufferedIOBase) and src.seekable():
        here = src.tell()
        try:
            return src.seek(0, SEEK_END)
        finally:
            src.seek(here)
    return None


def name_of_src(src: str | bytes | Path | BufferedIOBase) -> str:
    if isinstance(src, (str, Path)):
        return Path(src).name
    return f"<{type(src).__name__}>"
