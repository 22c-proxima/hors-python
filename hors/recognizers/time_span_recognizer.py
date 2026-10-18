"""
Recognizer for duration phrases ('через 2 дня', 'час назад').
"""

from datetime import datetime, timedelta
from re import Match

from .recognizer import Recognizer
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from ..utils import ParserUtils
from .recognizer import Recognizer


class TimeSpanRecognizer(Recognizer):
    """
    Recognizes duration phrases: 'через 2 дня', 'спустя час', '3 недели назад'
    (pattern (i)?((0?[Ymwdhe]N?)+)([bl])?).

    The phrase must contain exactly one of the prefix 'через' ('i') or the postfix
    'назад'/'спустя' ('b'/'l'); a bare duration without either is rejected.
    """
    regex_pattern = r'(i)?((0?[Ymwdhe]N?)+)([bl])?'

    def parse_match(self, data: DatesRawData, match: Match[str], now: datetime) -> bool:
        """
        Build a span period from a sequence of number + period-word pairs.

        The offset starts at `now` and each unit shifts it forward (or backward for
        'назад'): 'Y' years, 'm' months, 'w' weeks, 'd' days, 'h' hours, 'e' minutes;
        the fix level tightens as units get smaller (MONTH -> WEEK -> DAY -> TIME).
        Month offsets are normalized across year boundaries, and both the resulting
        day and year are clamped into their valid ranges. The resulting period
        carries span = offset - now and its date is the end of the span; all
        matched slots are replaced by it.

        Returns:
            True when exactly one of 'через' / postfix is present, otherwise False.
        """
        if (match.group(1) is None) != (match.group(4) is None):  # ибо приоритет is ниже =(
            letters = list(match.group(2))
            last_number = 1
            token_index = match.start(2)
            direction = 1
            if match.group(4) == 'b':
                direction = -1

            date = AbstractPeriod(span_direction=direction)
            offset = now

            for l in letters:
                if l == '0':
                    try:
                        last_number = int(data.tokens[token_index].value)
                    except ValueError:
                        last_number = 0
                elif l == 'Y':
                    new_year = max(1, min(9999, offset.year + direction*last_number))
                    day = ParserUtils.get_day_valid_for_month(new_year, offset.month, offset.day)
                    offset = offset.replace(year=new_year, day=day)
                    date.fix_down_to(FixPeriod.MONTH)
                    last_number = 1
                elif l == 'm':
                    months = offset.month + direction*last_number
                    year_delta, new_month = divmod(months - 1, 12)
                    new_month += 1
                    new_year = max(1, min(9999, offset.year + year_delta))
                    day = ParserUtils.get_day_valid_for_month(new_year, new_month, offset.day)
                    offset = offset.replace(year=new_year, month=new_month, day=day)
                    date.fix_down_to(FixPeriod.WEEK)
                    last_number = 1
                elif l == 'w':
                    offset += timedelta(days=7*direction*last_number)
                    date.fix_down_to(FixPeriod.DAY)
                    last_number = 1
                elif l == 'd':
                    offset += timedelta(days=direction*last_number)
                    date.fix_down_to(FixPeriod.DAY)
                    last_number = 1
                elif l == 'h':
                    offset += timedelta(seconds=60*60*direction*last_number)
                    date.fix_down_to(FixPeriod.TIME)
                    last_number = 1
                elif l == 'e':
                    offset += timedelta(seconds=60*direction*last_number)
                    date.fix_down_to(FixPeriod.TIME)
                token_index += 1
            # for l in letters:

            date.date = datetime(offset.year, offset.month, offset.day)
            if date.is_fixed(FixPeriod.TIME):
                date.time = timedelta(seconds=60*60*offset.hour + 60*offset.minute)
            date.span = offset - now

            s, e = match.span()
            data.replace_tokens_by_dates(s, (e - s), date)

            return True
        # if match.group(1) is None != match.group(4) is None:
        return False
