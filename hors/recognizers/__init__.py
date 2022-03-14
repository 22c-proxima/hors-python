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
