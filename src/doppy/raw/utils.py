from io import BufferedIOBase
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
