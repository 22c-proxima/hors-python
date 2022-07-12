from datetime import timedelta

from .recognizer import Recognizer
from ..models import AbstractPeriod, DatesRawData
from ..models.parser_models import FixPeriod
from .recognizer import Recognizer


class PartOfDayRecognizer(Recognizer):
    regex_pattern = r'(@)?f?([ravgdn])f?(@)?'

    def parse_match(self, data: DatesRawData, match, _) -> bool:
        if (match.group(1) is not None) or (match.group(3) is not None):
            hours = 0
            m = match.group(2)
            if m == 'r':
                hours = 9
            elif m in ['a', 'd', 'n']:
                hours = 12
            elif m == 'v':
                hours = 17
            elif m == 'g':
                hours = 23

            if hours != 0:
                date = AbstractPeriod(time=timedelta(seconds=hours*60*60))
                date.fix(FixPeriod.TIME_UNCERTAIN)

                start = match.span()[0]
                length = match.span()[1] - start - 1
                if match.group(1) is not None:
                    start += 1
                    if match.group(3) is not None:
                        length -= 1
                data.replace_tokens_by_dates(start, length, date)

                return True
        # if match.group(1) is not None and match.group(3) is not None:

        return False
