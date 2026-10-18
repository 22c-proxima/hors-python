"""
Recognizer for clock-time phrases ('в 3 часа', '9 вечера').
"""

from datetime import datetime, timedelta
from re import Match

from .recognizer import Recognizer
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from .recognizer import Recognizer


class TimeRecognizer(Recognizer):
    """
    Recognizes clock-time phrases (pattern ([rvgd])?([fot])?(Q|H)?(h|(0)(h)?)((0)e?)?([rvgd])?):
    an optional part-of-day word, a preposition ('в'/'с'/'на'/'до'/'по'), 'четверть/половина',
    an hour number or the word 'час'/'ч', an optional minute number and an optional
    trailing part-of-day word.

    Examples: 'в 3 часа', '9 вечера', '24'.
    """
    regex_pattern = r'([rvgd])?([fot])?(Q|H)?(h|(0)(h)?)((0)e?)?([rvgd])?'

    def parse_match(self, data: DatesRawData, match: Match[str], now: datetime) -> bool:
        """
        Convert a matched time phrase into a TIME period.

        Hours are taken from the explicit number (group 5) or default to 1 for
        'четверть/половина часа' phrases; minutes come from the trailing number
        (group 8, 0..59) or from quarter/half: Q -> :15 of the previous hour,
        H -> :30.

        Values above 12 are taken as-is (FixPeriod.TIME). Otherwise a part-of-day
        word pins the time: 'вечер' adds 12 when hours <= 11, 'ночь' adds 12 when
        hours >= 10, 'днём' adds 12 when hours <= 4; 24 wraps to 0. Hours outside
        0..23 reject the match so the phrase is left for other recognizers.

        If the phrase started with 'до/по', that token is returned to the stream so
        a time range ('с 5 до 7') can be built later. All matched slots are replaced
        by a single date.

        Returns:
            True when an hour could be determined, otherwise False (the match is
            left for other recognizers).
        """
        if match.group(5) is not None or match.group(6) is not None or match.group(4) is not None or match.group(1) is not None or match.group(9):
            if match.group(5) is None:
                part_of_day = match.group(9) if match.group(9) is not None else (match.group(1) or '')
                if part_of_day not in ['d', 'g'] and match.group(2) is None:
                    return False

            hours = 1 if match.group(5) is None else int(data.tokens[match.start(5)].value)
            if hours == 24:
                hours = 0
            if 0 <= hours <= 23:
                minutes = 0
                if match.group(8) is not None:
                    m = int(data.tokens[match.start(8)].value)
                    if 0 <= m <= 59:
                        minutes = m
                elif match.group(3) is not None and hours > 0:
                    q = match.group(3)
                    if q == 'Q':
                        hours -= 1
                        minutes = 15
                    elif q == 'H':
                        hours -= 1
                        minutes = 30

                date = AbstractPeriod()
                date.fix(FixPeriod.TIME_UNCERTAIN)
                if hours > 12:
                    date.fix(FixPeriod.TIME)
                else:
                    part = 'd'
                    if match.group(9) is not None or match.group(1) is not None:
                        part = match.group(9) if match.group(1) is None else match.group(1)
                        date.fix(FixPeriod.TIME)
                    else:
                        date.fix(FixPeriod.TIME_UNCERTAIN)

                    if part == 'd':
                        if hours <= 4:
                            hours += 12
                    elif part == 'v':
                        if hours <= 11:
                            hours += 12
                    elif part == 'g':
                        if hours >= 10:
                            hours += 12

                date.time = timedelta(seconds=hours*60*60 + minutes*60)
                s, e = match.span()
                to_time = data.tokens[s]
                data.replace_tokens_by_dates(s, (e - s), date)
                if match.group(2) == 't':
                    data.return_tokens(s, 't', to_time)

                return True

            return False
        #  if match.group(5) is not None or match.group(6) is not None or match.group(4) is not None or match.group(1) is not None or match.group(9):

        return False
