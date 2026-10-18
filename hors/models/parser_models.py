"""
Data models shared between the parser and the recognizers: fix/period enums,
token types and the DateTimeToken result object.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum, auto

from .i_has_edges import IHasEdges


class FixPeriod(Enum):
    """
    Resolution levels of a date period, most specific first.

    Values are powers of two so that a set of fixed components can be stored
    as a bitmask (e.g. day + clock time = DAY | TIME). NONE means nothing is
    fixed yet. TIME and TIME_UNCERTAIN both fix the clock time: the former
    when it was stated explicitly ('в 15 часов'), the latter when only inferred
    (e.g. from 'утром' or 'вечером').
    """
    NONE           = 0
    TIME           = 1
    TIME_UNCERTAIN = 2
    DAY            = 4
    WEEK           = 8
    MONTH          = 16
    YEAR           = 32


class DateTimeTokenType(Enum):
    """
    Shape of a parsed date token.

    FIXED - a single point in time ('10 января', 'завтра в 5 часов');
    PERIOD - an interval with a start and an end ('с 5 до 7 вечера');
    SPAN_FORWARD / SPAN_BACKWARD - a duration counted from the reference
    moment, forward ('через 3 дня') or backward ('спустя 2 недели').
    """
    FIXED         = auto()
    PERIOD        = auto()
    SPAN_FORWARD  = auto()
    SPAN_BACKWARD = auto()


class PartTime(Enum):
    """
    Fractional clock offset mentioned in the phrase: QUARTER ('четверть') and
    HALF ('половина'), as in 'к четверти десятого'.
    """
    NONE    = auto()
    QUARTER = auto()
    HALF    = auto()


class RelativeMode(Enum):
    """
    Modifier of a relative date, i.e. which occurrence of the period is meant:
    PREVIOUS ('прошлый'), CURRENT ('этот' / 'текущий'), CURRENT_NEXT ('ближайший'),
    NEXT ('следующий'). NONE when no modifier was given.
    """
    NONE         = auto()
    NEXT         = auto()
    PREVIOUS     = auto()
    CURRENT      = auto()
    CURRENT_NEXT = auto()


class Period(Enum):
    """
    Duration units a span or period can be expressed in: MINUTE, HOUR, DAY,
    WEEK, MONTH, YEAR (NONE = no unit).
    """
    NONE   = auto()
    MINUTE = auto()
    HOUR   = auto()
    DAY    = auto()
    WEEK   = auto()
    MONTH  = auto()
    YEAR   = auto()


class DayTime(Enum):
    """
    Part of the day referenced by the phrase: MORNING ('утро'), NOON ('полдень'),
    DAY ('день'), EVENING ('вечер'), NIGHT ('ночь'). NONE when not stated.
    """
    NONE    = auto()
    MORNING = auto()
    NOON    = auto()
    DAY     = auto()
    EVENING = auto()
    NIGHT   = auto()


# Number of bits needed to represent any FixPeriod value (bitmask width).
MAX_PERIOD: int = max(p.value for p in FixPeriod).bit_length()


class DateTimeToken(IHasEdges):
    """
    A single parsed date/time expression with its position in the source phrase.

    Fields:
        type: the shape of the token (see DateTimeTokenType);
        date_from: start of the interval, or the moment itself for points;
        date_to: end of the interval (equals date_from for points);
        span: duration for SPAN_FORWARD / SPAN_BACKWARD tokens, else None;
        has_time: True when a clock time is part of the token.

    start/end (inherited from IHasEdges) are character offsets into the source
    phrase, so source_text[start:end] is the exact matched expression.
    """
    type: Optional[DateTimeTokenType] = None
    date_from: datetime = datetime.now()
    date_to: datetime = datetime.now()
    span: Optional[timedelta] = None
    has_time: bool = False

    __duplicate_group: int = -1

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the token to a plain dict.

        Returns:
            A JSON-serializable dict with keys 'type', 'date_from' and 'date_to'
            (ISO format), 'span', 'has_time', 'start', 'end'.
        """
        return {
            'type': str(self.type),
            'date_from': self.date_from.isoformat(),
            'date_to': self.date_to.isoformat(),
            'span': str(self.span),
            'has_time': self.has_time,
            'start': self.start,
            'end': self.end
        }

    def overlapping_with(self, other: "DateTimeToken") -> bool:
        """
        Check whether this token overlaps another one in the source phrase.

        Args:
            other: The other token to compare against.

        Returns:
            True when either edge of `other` falls inside this token's [start, end] range.
        """
        start_between = self.start <= other.start <= self.end
        end_between = self.start <= other.end <= self.end
        return start_between or end_between

    def set_duplicate_group(self, d: int) -> None:
        """
        Assign the duplicate-group id; -1 means the token stands alone.

        Tokens merged from several source expressions share one group id, and
        only the first of each group survives in HorsParseResult.dates.
        """
        self.__duplicate_group = d

    def get_duplicate_group(self) -> int:
        """
        Returns:
            The duplicate-group id (-1 when the token stands alone).
        """
        return self.__duplicate_group

    def __str__(self) -> str:
        """
        Human-readable representation of the token (type, dates, span, offsets).
        """
        return f'[Type={ self.type }, From={ self.date_from.isoformat() }, To={ self.date_to.isoformat() }, ' +\
            f'Span={ self.span }, HasTime={ self.has_time }, StartIndex={ self.start }, EndIndex={ self.end }]'
