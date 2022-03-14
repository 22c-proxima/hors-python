from typing import Dict, Optional
from re import sub

from ..dict import Keywords, Morph
from ..models.parser_models import (
    Period,
    RelativeMode,
    DayTime,
    PartTime
)


PERIOD_MAPPING: Dict[Period, str] = {
    Period.MINUTE: 'e',
    Period.HOUR:   'h',
    Period.DAY:    'd',
    Period.WEEK:   'w',
    Period.MONTH:  'm'
}

RELATIVE_MODE_MAPPING: Dict[RelativeMode, str] = {
    RelativeMode.PREVIOUS:     's',
    RelativeMode.CURRENT:      'u',
    RelativeMode.CURRENT_NEXT: 'y',
    RelativeMode.NEXT:         'x'
}

DAYTIME_MAPPING: Dict[DayTime, str] = {
    DayTime.MORNING: 'r',
    DayTime.NOON:    'n',
    DayTime.DAY:     'a',
    DayTime.EVENING: 'v',
    DayTime.NIGHT:   'g'
}

PARTTIME_MAPPING: Dict[PartTime, str] = {
    PartTime.QUARTER: 'Q',
    PartTime.HALF:    'H'
}


class ParserExtractors:

    @staticmethod
    def create_pattern_from(token: str) -> str:
        t = sub(r'[^0-9а-яё-]', '', token.lower()).strip()

        if Morph.has_one_of_lemmas(t, Keywords.YEAR):
            return 'Y'
        if Morph.has_one_of_lemmas(t, Keywords.months()):
            return 'M'
        if Morph.has_one_of_lemmas(t, Keywords.days_of_week()):
            return 'D'
        if Morph.has_one_of_lemmas(t, Keywords.PREVIOUS_POSTFIX):
            return 'b'
        if Morph.has_one_of_lemmas(t, Keywords.AFTER_POSTFIX):
            return 'l'
        if Morph.has_one_of_lemmas(t, Keywords.AFTER):
            return 'i'
        if Morph.has_one_of_lemmas(t, Keywords.HOLIDAY):
            return 'W'

        p = period_from(t)
        if p is not None:
            return PERIOD_MAPPING[p]

        r = relative_mode_from(t)
        if r is not None:
            return RELATIVE_MODE_MAPPING[r]

        n = neighbour_days_from(t)
        if n is not None:
            return str(n + 4)

        d = daytime_from(t)
        if d is not None:
            return DAYTIME_MAPPING[d]

        pt = parttime_from(t)
        if pt is not None:
            return PARTTIME_MAPPING[pt]

        try:
            c = int(t)
            if 0 > c < 9999:
                return '_'
            return '1' if c > 1900 else '0'
        except:
            pass

        if Morph.has_one_of_lemmas(t, Keywords.TIME_FROM):
            return 'f'
        if Morph.has_one_of_lemmas(t, Keywords.TIME_TO):
            return 't'
        if Morph.has_one_of_lemmas(t, Keywords.TIME_ON):
            return 'o'
        if Morph.has_one_of_lemmas(t, Keywords.DAY_IN_MONTH):
            return '#'

        return 'N' if t == 'и' else '_'
    # def create_pattern_from(token: str) -> str:

# class ParserExtractors:


def period_from(t: str) -> Optional[Period]:
    if Morph.has_one_of_lemmas(t, Keywords.YEAR):
        return Period.YEAR
    if Morph.has_one_of_lemmas(t, Keywords.MONTH):
        return Period.MONTH
    if Morph.has_one_of_lemmas(t, Keywords.WEEK):
        return Period.WEEK
    if Morph.has_one_of_lemmas(t, Keywords.DAY):
        return Period.DAY
    if Morph.has_one_of_lemmas(t, Keywords.HOUR):
        return Period.HOUR
    if Morph.has_one_of_lemmas(t, Keywords.MINUTE):
        return Period.MINUTE
    return None


def relative_mode_from(t: str) -> Optional[RelativeMode]:
    if Morph.has_one_of_lemmas(t, Keywords.CURRENT):
        return RelativeMode.CURRENT
    if Morph.has_one_of_lemmas(t, Keywords.NEXT):
        return RelativeMode.NEXT
    if Morph.has_one_of_lemmas(t, Keywords.PREVIOUS):
        return RelativeMode.PREVIOUS
    if Morph.has_one_of_lemmas(t, Keywords.CURRENT_NEXT):
        return RelativeMode.CURRENT_NEXT
    return None


def neighbour_days_from(t: str) -> Optional[int]:
    if Morph.has_one_of_lemmas(t, Keywords.TOMORROW):
        return 1
    if Morph.has_one_of_lemmas(t, Keywords.TODAY):
        return 0
    if Morph.has_one_of_lemmas(t, Keywords.AFTER_TOMORROW):
        return 2
    if Morph.has_one_of_lemmas(t, Keywords.YESTERDAY):
        return -1
    if Morph.has_one_of_lemmas(t, Keywords.BEFORE_YESTERDAY):
        return -2
    return None


def daytime_from(t: str) -> Optional[DayTime]:
    if Morph.has_one_of_lemmas(t, Keywords.NOON):
        return DayTime.NOON
    if Morph.has_one_of_lemmas(t, Keywords.MORNING):
        return DayTime.MORNING
    if Morph.has_one_of_lemmas(t, Keywords.EVENING):
        return DayTime.EVENING
    if Morph.has_one_of_lemmas(t, Keywords.NIGHT):
        return DayTime.NIGHT
    if Morph.has_one_of_lemmas(t, Keywords.DAYTIME_DAY):
        return DayTime.DAY
    return None


def parttime_from(t: str) -> Optional[PartTime]:
    if Morph.has_one_of_lemmas(t, Keywords.QUARTER):
        return PartTime.QUARTER
    if Morph.has_one_of_lemmas(t, Keywords.HALF):
        return PartTime.HALF
    return None
