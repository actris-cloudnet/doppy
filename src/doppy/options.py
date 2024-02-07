from enum import Enum


class BgCorrectionMethod(Enum):
    FIT = "fit"
    MEAN = "mean"
    PRE_COMPUTED = "pre_computed"


class BgFitMethod(Enum):
    LIN = "lin"
    EXP = "exp"
    EXPLIN = "explin"
