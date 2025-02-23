from typing import Dict, Any
from datetime import datetime, timedelta
from enum import Enum, auto

from .i_has_edges import IHasEdges


class FixPeriod(Enum):
    NONE           = 0
    TIME           = 1
    TIME_UNCERTAIN = 2
    DAY            = 4
    WEEK           = 8
    MONTH          = 16
    YEAR           = 32


class DateTimeTokenType(Enum):
    FIXED         = auto()
    PERIOD        = auto()
    SPAN_FORWARD  = auto()
    SPAN_BACKWARD = auto()


class PartTime(Enum):
    NONE    = auto()
    QUARTER = auto()
    HALF    = auto()


class RelativeMode(Enum):
    NONE         = auto()
    NEXT         = auto()
    PREVIOUS     = auto()
    CURRENT      = auto()
    CURRENT_NEXT = auto()


class Period(Enum):
    NONE   = auto()
    MINUTE = auto()
    HOUR   = auto()
    DAY    = auto()
    WEEK   = auto()
    MONTH  = auto()
    YEAR   = auto()


class DayTime(Enum):
    NONE    = auto()
    MORNING = auto()
    NOON    = auto()
    DAY     = auto()
    EVENING = auto()
    NIGHT   = auto()


MAX_PERIOD: int = max(p.value for p in FixPeriod).bit_length()


class DateTimeToken(IHasEdges):
    type: DateTimeTokenType = None
    date_from: datetime = datetime.now()
    date_to: datetime = datetime.now()
    span: timedelta = None
    has_time: bool = False

    __duplicate_group: int = -1

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': str(self.type),
            'date_from': self.date_from.isoformat(),
            'date_to': self.date_to.isoformat(),
            'span': str(self.span),
            'has_time': self.has_time,
            'start': self.start,
            'end': self.end
        }

    def overlapping_with(self, other) -> bool:
        start_between = self.start <= other.start <= self.end
        end_between = self.start <= other.end <= self.end
        return start_between or end_between

    def set_duplicate_group(self, d: int) -> None:
        self.__duplicate_group = d

    def get_duplicate_group(self) -> int:
        return self.__duplicate_group

    def __str__(self) -> str:
        return f'[Type={ self.type }, From={ self.date_from.isoformat() }, To={ self.date_to.isoformat() }, ' +\
            f'Span={ self.span }, HasTime={ self.has_time }, StartIndex={ self.start }, EndIndex={ self.end }]'
