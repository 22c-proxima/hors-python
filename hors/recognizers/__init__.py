"""All date-expression recognizers, in execution priority order.

HorsTextParser runs the list `recognizers` one after another against the same
DatesRawData; each recognizer claims its own regex matches and turns them into
AbstractPeriod slots, so earlier entries win over later ones when two
recognizers could match the same words.
"""
from typing import List

from .recognizer import Recognizer

from .holidays_recognizer import HolidaysRecognizer
from .dates_period_recognizer import DatesPeriodRecognizer
from .days_month_recognizer import DaysMonthRecognizer
from .month_recognizer import MonthRecognizer
from .relative_day_recognizer import RelativeDayRecognizer
from .time_span_recognizer import TimeSpanRecognizer
from .year_recognizer import YearRecognizer
from .relative_date_recognizer import RelativeDateRecognizer
from .day_of_week_recognizer import DayOfWeekRecognizer
from .time_recognizer import TimeRecognizer
from .part_of_day_recognizer import PartOfDayRecognizer


recognizers: List[Recognizer] = [
    HolidaysRecognizer(),
    DatesPeriodRecognizer(),
    DaysMonthRecognizer(),
    MonthRecognizer(),
    RelativeDayRecognizer(),
    TimeSpanRecognizer(),
    YearRecognizer(),
    RelativeDateRecognizer(),
    DayOfWeekRecognizer(),
    TimeRecognizer(),
    PartOfDayRecognizer()
]


__all__ = [
    'recognizers',
    'Recognizer',
    'HolidaysRecognizer',
    'DatesPeriodRecognizer',
    'DaysMonthRecognizer',
    'MonthRecognizer',
    'RelativeDayRecognizer',
    'TimeSpanRecognizer',
    'YearRecognizer',
    'RelativeDateRecognizer',
    'DayOfWeekRecognizer',
    'TimeRecognizer',
    'PartOfDayRecognizer',
]
