"""
Maps raw tokens to the one-character pattern codes that recognizers' regexes are built from.

Pattern characters produced by ParserExtractors.create_pattern_from:
    Y - year word ('год'), M - month name, D - weekday name;
    b - 'назад', l - 'спустя', i - 'через', W - 'выходной';
    e/h/d/w/m - minute/hour/day/week/month period words;
    s/u/y/x - previous/current/current-next/next relative modes;
    2..6 - two-days-ago .. day-after-tomorrow (3 today, 4 tomorrow);
    r/n/a/v/g - morning/noon/daytime/evening/night;
    Q/H - quarter/half of an hour;
    1 - number > 1900 (a full year), 0 - any other non-negative number, _ - negative or unknown;
    f/t/o - 'в|с' / 'до|по' / 'на'; # - 'число'; N - conjunction 'и'.
"""

from typing import Dict, Optional
from re import sub

from ..dict import Keywords, Morph
from ..models.parser_models import (
    Period,
    RelativeMode,
    DayTime,
    PartTime
)


# Period word -> pattern character.
PERIOD_MAPPING: Dict[Period, str] = {
    Period.MINUTE: 'e',
    Period.HOUR:   'h',
    Period.DAY:    'd',
    Period.WEEK:   'w',
    Period.MONTH:  'm'
}

# Relative mode word -> pattern character.
RELATIVE_MODE_MAPPING: Dict[RelativeMode, str] = {
    RelativeMode.PREVIOUS:     's',
    RelativeMode.CURRENT:      'u',
    RelativeMode.CURRENT_NEXT: 'y',
    RelativeMode.NEXT:         'x'
}

# Part-of-day word -> pattern character.
DAYTIME_MAPPING: Dict[DayTime, str] = {
    DayTime.MORNING: 'r',
    DayTime.NOON:    'n',
    DayTime.DAY:     'a',
    DayTime.EVENING: 'v',
    DayTime.NIGHT:   'g'
}

# Fraction-of-an-hour word -> pattern character.
PARTTIME_MAPPING: Dict[PartTime, str] = {
    PartTime.QUARTER: 'Q',
    PartTime.HALF:    'H'
}


class ParserExtractors:
    """Converts a single token into its one-character pattern code (see module docstring)."""

    @staticmethod
    def create_pattern_from(token: str) -> str:
        """
        Reduce a token to a single pattern character.

        Checks, in order: year/month/weekday words, 'назад'/'спустя'/'через',
        'выходной', period words, relative modes, neighbour-day words (сегодня etc.),
        parts of day, hour fractions, then the numeric value itself ('1' for numbers
        above 1900, '0' otherwise, '_' for negatives), prepositions, 'число' and
        finally 'N' for 'и' / '_' for anything unrecognized.
        """
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
    """Map a token to the Period it names (minute/hour/day/week/month), None if none."""
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
    """Map a token to the RelativeMode it names (current/next/previous/current-next)."""
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
    """Map today/yesterday-ish words to an offset in days from today (-2..+2)."""
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
    """Map a part-of-day word (утро/полдень/днём/вечер/ночь) to DayTime."""
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
    """Map a fraction-of-an-hour word (четверть/половина) to PartTime."""
    if Morph.has_one_of_lemmas(t, Keywords.QUARTER):
        return PartTime.QUARTER
    if Morph.has_one_of_lemmas(t, Keywords.HALF):
        return PartTime.HALF
    return None
