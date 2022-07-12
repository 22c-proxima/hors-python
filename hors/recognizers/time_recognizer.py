from datetime import datetime, timedelta

from .recognizer import Recognizer
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from .recognizer import Recognizer


class TimeRecognizer(Recognizer):
    regex_pattern = r'([rvgd])?([fot])?(Q|H)?(h|(0)(h)?)((0)e?)?([rvgd])?'

    def parse_match(self, data: DatesRawData, match, now: datetime) -> bool:
        if match.group(5) is not None or match.group(6) is not None or match.group(4) is not None or match.group(1) is not None or match.group(9):
            if match.group(5) is None:
                part_of_day = match.group(9) if match.group(9) is not None else (match.group(1) or '')
                if part_of_day not in ['d', 'g'] and match.group(2) is None:
                    return False

            hours = 1 if match.group(5) is None else int(data.tokens[match.start(5)].value)
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

                    if hours == 24:
                        hours = 0

                date.time = timedelta(seconds=hours*60*60 + minutes*60)
                s, e = match.span()
                to_time = data.tokens[s]
                data.replace_tokens_by_dates(s, (e - s), date)
                if match.group(2) == 't':
                    data.return_tokens(s, 't', to_time)
            # if 0 <= hours <= 23:

            return True
        #  if match.group(5) is not None or match.group(6) is not None or match.group(4) is not None or match.group(1) is not None or match.group(9):

        return False
