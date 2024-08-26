class DoppyException(Exception):
    pass


class RawParsingError(DoppyException):
    pass


class NoDataError(DoppyException):
    pass


class ShapeError(DoppyException):
    pass
