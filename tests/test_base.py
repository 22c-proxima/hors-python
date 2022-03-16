import unittest
from datetime import datetime

from hors import process_phrase
from hors.models.parser_models import DateTimeTokenType


class BaseHorsTests(unittest.TestCase):

    def test_january(self):
        result = process_phrase('10 января событие', datetime(2019, 10, 13))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(10, date.date_from.day)
        self.assertEqual(1, date.date_from.month)
        self.assertEqual(2020, date.date_from.year)

    def test_time_period_before_day(self):
        result = process_phrase(
            'с 5 до 7 вечера в понедельник будет событие',
            datetime(2019, 10, 13)
        )
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(17, date.date_from.hour)
        self.assertEqual(19, date.date_to.hour)
        self.assertEqual(14, date.date_from.day)
        self.assertEqual(14, date.date_to.day)

    def test_time_period_simple(self):
        result = process_phrase('с 10 до 13 событие', datetime(2019, 10, 13))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.PERIOD, date.type)
        self.assertEqual(10, date.date_from.hour)
        self.assertEqual(13, date.date_to.hour)

    def test_daytime(self):
        result = process_phrase(
            'Завтра в час обед и продлится он час с небольшим',
            datetime(2019, 10, 14)
        )
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(13, date.date_from.hour)

    def test_nighttime(self):
        result = process_phrase(
            'Завтра в 2 ночи полнолуние, а затем в 3 часа ночи новолуние и наконец в 12 часов ночи игра.',
            datetime(2020, 1, 1)
        )
        self.assertEqual(3, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(2, date.date_from.hour)

        date = result.dates[1]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(3, date.date_from.hour)

        date = result.dates[2]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(0, date.date_from.hour)
        self.assertEqual(1, date.date_from.day)

    def test_long_period(self):
        result = process_phrase(
            'С вечера следующей среды до четверти 10 утра понедельника в декабре можно будет наблюдать снег',
            datetime(2019, 10, 14)
        )
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.PERIOD, date.type)
        self.assertEqual(2019, date.date_from.year)
        self.assertEqual(23, date.date_from.day)
        self.assertEqual(10, date.date_from.month)
        self.assertEqual(2, date.date_to.day)
        self.assertEqual(12, date.date_to.month)
        self.assertEqual(9, date.date_to.hour)
        self.assertEqual(15, date.date_to.minute)

    def test_collapse_complex(self):
        result = process_phrase(
            'В понедельник в 9 и 10 вечера', datetime(2019, 10, 13)
        )
        self.assertEqual(2, len(result.dates))

        date = result.dates[0]
        self.assertEqual(2019, date.date_from.year)
        self.assertEqual(14, date.date_from.day)
        self.assertEqual(21, date.date_from.hour)

        date = result.dates[1]
        self.assertEqual(14, date.date_from.day)
        self.assertEqual(22, date.date_from.hour)

        result = process_phrase(
            'В понедельник в 10 и 9 вечера', datetime(2019, 10, 13)
        )
        self.assertEqual(2, len(result.dates))

        date = result.dates[0]
        self.assertEqual(2019, date.date_from.year)
        self.assertEqual(14, date.date_from.day)
        self.assertEqual(22, date.date_from.hour)

        date = result.dates[1]
        self.assertEqual(14, date.date_from.day)
        self.assertEqual(21, date.date_from.hour)

    def test_multiple_simple(self):
        result = process_phrase(
            'Позавчера в 6:30 состоялось совещание, а завтра днём будет хорошая погода.',
            datetime(2019, 10, 13)
        )
        self.assertEqual(2, len(result.dates))

        date = result.dates[0]
        self.assertEqual(2019, date.date_from.year)
        self.assertEqual(11, date.date_from.day)
        self.assertEqual(6, date.date_from.hour)
        self.assertEqual(30, date.date_from.minute)

        date = result.dates[1]
        self.assertEqual(2019, date.date_from.year)
        self.assertEqual(14, date.date_from.day)
        self.assertEqual(True, date.has_time)

    def test_collapse_direction(self):
        strings = [
            'В следующем месяце с понедельника буду ходить в спортзал!',
            'С понедельника в следующем месяце буду ходить в спортзал!',
        ]
        for s in strings:
            result = process_phrase(s, datetime(2019, 10, 15))
            self.assertEqual(1, len(result.dates))

            date = result.dates[0]
            self.assertEqual(2019, date.date_from.year)
            self.assertEqual(4, date.date_from.day)
            self.assertEqual(11, date.date_from.month)

    def test_weekday(self):
        result = process_phrase(
            'В следующем месяце во вторник состоится событие',
            datetime(2019, 10, 13)
        )
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(2019, date.date_from.year)
        self.assertEqual(5, date.date_from.day)
        self.assertEqual(11, date.date_from.month)

        result = process_phrase(
            'Через месяц во вторник состоится событие',
            datetime(2019, 10, 13)
        )
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(2019, date.date_from.year)
        self.assertEqual(12, date.date_from.day)
        self.assertEqual(11, date.date_from.month)

    def test_time_after_day(self):
        result = process_phrase('в четверг 16 0 0 будет событие', datetime(2019, 10, 8))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(True, date.has_time)
        self.assertEqual(16, date.date_from.hour)
        self.assertEqual(10, date.date_from.day)

    def test_time_period(self):
        result = process_phrase(
            'В следующий четверг с 9 утра до 6 вечера важный экзамен!',
            datetime(2019, 9, 7)
        )
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(True, date.has_time)
        self.assertEqual(9, date.date_from.hour)
        self.assertEqual(12, date.date_from.day)
        self.assertEqual(9, date.date_from.month)
        self.assertEqual(18, date.date_to.hour)
        self.assertEqual(12, date.date_to.day)
        self.assertEqual(9, date.date_to.month)
        self.assertEqual(2019, date.date_from.year)
        self.assertEqual(2019, date.date_to.year)

    def test_complex_period(self):
        result = process_phrase(
            'хакатон с 12 часов 18 сентября до 12 часов 20 сентября',
            datetime(2019, 7, 7)
        )
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.PERIOD, date.type)
        self.assertEqual(True, date.has_time)
        self.assertEqual(12, date.date_from.hour)
        self.assertEqual(18, date.date_from.day)
        self.assertEqual(9, date.date_from.month)
        self.assertEqual(12, date.date_to.hour)
        self.assertEqual(20, date.date_to.day)
        self.assertEqual(9, date.date_to.month)
        self.assertEqual(2019, date.date_from.year)
        self.assertEqual(2019, date.date_to.year)

    def test_time_before_day(self):
        result = process_phrase(
            '12 часов 12 сентября будет встреча',
            datetime(2019, 9, 7)
        )
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(True, date.has_time)
        self.assertEqual(12, date.date_from.hour)
        self.assertEqual(12, date.date_from.day)
        self.assertEqual(9, date.date_from.month)

    def test_time_hour_of_day(self):
        result = process_phrase('24 сентября в час дня', datetime(2019, 9, 7))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(True, date.has_time)
        self.assertEqual(13, date.date_from.hour)

    def test_fix_period(self):
        result = process_phrase('на выходных будет хорошо', datetime(2019, 9, 7))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.PERIOD, date.type)
        self.assertEqual(14, date.date_from.day)
        self.assertEqual(15, date.date_to.day)

    def test_dates_period(self):
        strings = [
            'с 11 по 15 сентября будет командировка',
            '11 по 15 сентября будет командировка',
            'с 11 до 15 сентября будет командировка',
        ]
        for s in strings:
            result = process_phrase(s, datetime(2019, 8, 6))
            self.assertEqual(1, len(result.dates))

            date = result.dates[0]
            self.assertEqual(DateTimeTokenType.PERIOD, date.type)
            self.assertEqual(11, date.date_from.day)
            self.assertEqual(15, date.date_to.day)
            self.assertEqual(9, date.date_from.month)
            self.assertEqual(9, date.date_to.month)

        result = process_phrase('с 11 до 15 числа будет командировка', datetime(2019, 9, 6))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.PERIOD, date.type)
        self.assertEqual(11, date.date_from.day)
        self.assertEqual(15, date.date_to.day)
        self.assertEqual(9, date.date_from.month)
        self.assertEqual(9, date.date_to.month)

    def test_days_of_week(self):
        result = process_phrase('во вторник встреча с заказчиком', datetime(2019, 9, 6))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(10, date.date_from.day)

    def test_holidays(self):
        result = process_phrase('в эти выходные еду на дачу', datetime(2019, 9, 2))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.PERIOD, date.type)
        self.assertEqual(7, date.date_from.day)
        self.assertEqual(8, date.date_to.day)

    def test_holiday(self):
        result = process_phrase('пойду гулять в следующий выходной', datetime(2019, 9, 2))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(14, date.date_from.day)
        self.assertEqual(14, date.date_to.day)


if __name__ == '__main__':
    unittest.main()
