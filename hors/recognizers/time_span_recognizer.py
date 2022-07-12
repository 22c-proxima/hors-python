from datetime import datetime, timedelta

from .recognizer import Recognizer
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from .recognizer import Recognizer


class TimeSpanRecognizer(Recognizer):
    regex_pattern = r'(i)?((0?[Ymwdhe]N?)+)([bl])?'

    def parse_match(self, data: DatesRawData, match, now: datetime) -> bool:
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
                    offset = offset.replace(year=offset.year + direction*last_number)
                    date.fix_down_to(FixPeriod.MONTH)
                    last_number = 1
                elif l == 'm':
                    offset = offset.replace(month=offset.month + direction*last_number)
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
