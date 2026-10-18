import unittest
from datetime import datetime

from hors import process_phrase
from hors.models.parser_models import DateTimeTokenType


class EdgeCaseHorsTests(unittest.TestCase):

    # --- Leap years and end-of-month clamping ---

    def test_leap_day_in_common_year(self):
        result = process_phrase('29 февраля', datetime(2023, 1, 1))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(datetime(2023, 2, 28), date.date_from)
        self.assertEqual(datetime(2023, 2, 28, 23, 59, 59, 999999), date.date_to)

    def test_leap_day_in_leap_year(self):
        result = process_phrase('29 февраля', datetime(2024, 1, 1))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(datetime(2024, 2, 29), date.date_from)
        self.assertEqual(datetime(2024, 2, 29, 23, 59, 59, 999999), date.date_to)

    def test_thirty_first_of_june(self):
        result = process_phrase('31 июня', datetime(2024, 6, 15))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(datetime(2024, 6, 30), date.date_from)
        self.assertEqual(datetime(2024, 6, 30, 23, 59, 59, 999999), date.date_to)

    def test_thirty_first_february_in_common_year(self):
        result = process_phrase('31 февраля', datetime(2023, 1, 1))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(datetime(2023, 2, 28), date.date_from)
        self.assertEqual(datetime(2023, 2, 28, 23, 59, 59, 999999), date.date_to)

    # --- Multiple days: "N и M числа" ---

    def test_two_days_by_number(self):
        result = process_phrase('5 и 6 числа', datetime(2024, 9, 10))
        self.assertEqual(2, len(result.dates))

        first, second = result.dates
        self.assertEqual(DateTimeTokenType.FIXED, first.type)
        self.assertEqual(datetime(2024, 9, 5), first.date_from)
        self.assertEqual(datetime(2024, 9, 6), second.date_from)

    def test_two_days_by_number_in_december(self):
        # Documents current behavior: the rollover branch in DaysMonthRecognizer
        # is dead code, so both days stay in December instead of shifting to January.
        result = process_phrase('5 и 6 числа', datetime(2024, 12, 10))
        self.assertEqual(2, len(result.dates))

        first, second = result.dates
        self.assertEqual(datetime(2024, 12, 5), first.date_from)
        self.assertEqual(datetime(2024, 12, 6), second.date_from)

    def test_overflow_day_and_small_day_in_february(self):
        result = process_phrase('30 и 1 числа', datetime(2024, 2, 10))
        self.assertEqual(2, len(result.dates))

        first, second = result.dates
        self.assertEqual(datetime(2024, 2, 29), first.date_from)
        self.assertEqual(datetime(2024, 2, 1), second.date_from)

    # --- Weekday boundaries (now is Monday) ---

    def test_tuesday_from_monday_is_next_day(self):
        result = process_phrase('во вторник', datetime(2024, 11, 11))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(datetime(2024, 11, 12), date.date_from)

    def test_previous_monday_from_monday_is_last_week(self):
        result = process_phrase('в прошлый понедельник', datetime(2024, 11, 11))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(datetime(2024, 11, 4), date.date_from)

    def test_next_monday_from_monday_is_next_week(self):
        result = process_phrase('в следующий понедельник', datetime(2024, 11, 11))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(datetime(2024, 11, 18), date.date_from)

    # --- Relative spans ---

    def test_relative_span_with_fixed_weekday(self):
        result = process_phrase('через 2 недели в прошлый вторник', datetime(2024, 11, 11))
        self.assertEqual(2, len(result.dates))

        span, fixed = result.dates
        self.assertEqual(DateTimeTokenType.SPAN_FORWARD, span.type)
        self.assertEqual(datetime(2024, 11, 25), span.date_from)
        self.assertEqual(DateTimeTokenType.FIXED, fixed.type)
        self.assertEqual(datetime(2024, 11, 5), fixed.date_from)

    def test_backward_two_months_span(self):
        result = process_phrase('2 месяца назад', datetime(2024, 7, 15))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.SPAN_BACKWARD, date.type)
        # The offset (May 15) is expanded to the week window it falls into.
        self.assertEqual(datetime(2024, 5, 13), date.date_from)
        self.assertEqual(datetime(2024, 5, 19, 23, 59, 59, 999999), date.date_to)

    def test_forward_15_months_normalizes_year(self):
        result = process_phrase('через 15 месяцев', datetime(2024, 10, 15))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.SPAN_FORWARD, date.type)
        # October + 15 months rolls over into January of the year after next.
        self.assertEqual(datetime(2026, 1, 12), date.date_from)
        self.assertEqual(datetime(2026, 1, 18, 23, 59, 59, 999999), date.date_to)

    def test_backward_years_below_one_clamp_to_year_one(self):
        result = process_phrase('600 лет назад', datetime(500, 1, 15))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.SPAN_BACKWARD, date.type)
        # Year cannot go below 1: the offset clamps to January of year 1.
        self.assertEqual(datetime(1, 1, 1), date.date_from)
        self.assertEqual(datetime(1, 1, 31, 23, 59, 59, 999999), date.date_to)

    def test_forward_eight_years_span(self):
        result = process_phrase('через 8 лет', datetime(2024, 10, 1))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.SPAN_FORWARD, date.type)
        self.assertEqual(datetime(2032, 10, 1), date.date_from)
        self.assertEqual(datetime(2032, 10, 31, 23, 59, 59, 999999), date.date_to)

    # --- Time edge cases ---

    def test_bare_number_as_time(self):
        result = process_phrase('5', datetime(2024, 7, 1))
        self.assertEqual(1, len(result.dates))
        self.assertEqual(datetime(2024, 7, 1, 5, 0), result.dates[0].date_from)

        result = process_phrase('3', datetime(2024, 7, 1))
        self.assertEqual(1, len(result.dates))
        # Without a part-of-day word, hours <= 4 are assumed to be PM.
        self.assertEqual(datetime(2024, 7, 1, 15, 0), result.dates[0].date_from)

    def test_hour_24_wraps_to_zero(self):
        result = process_phrase('в 24', datetime(2024, 7, 1))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        # '24' is treated the same as '0'.
        self.assertEqual(datetime(2024, 7, 1, 12, 0), date.date_from)

    def test_hour_25_is_not_a_time(self):
        result = process_phrase('в 25', datetime(2024, 7, 1))
        self.assertEqual(0, len(result.dates))
        self.assertIn('25', result.text)

    def test_bare_25_hours_are_not_a_span(self):
        result = process_phrase('25 часов', datetime(2024, 7, 1))
        self.assertEqual(0, len(result.dates))

    # --- Typo robustness ---

    def test_weekday_typo_yields_no_date(self):
        result = process_phrase('в вторнник', datetime(2024, 11, 11))
        self.assertEqual(0, len(result.dates))

    def test_weekday_typo_does_not_break_valid_time(self):
        result = process_phrase('в вторнник в 5 утра', datetime(2024, 11, 11))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(datetime(2024, 11, 11, 5, 0), date.date_from)

    def test_empty_and_punctuation_only_input(self):
        for phrase in ['', '!!!?']:
            with self.subTest(phrase=phrase):
                result = process_phrase(phrase, datetime(2024, 7, 1))
                self.assertEqual(0, len(result.dates))

    # --- Documented limitations: unsupported word orders ---

    def test_nazad_before_number_is_treated_as_plain_time(self):
        # Documents current behavior: "назад N unit" is not a supported order;
        # the number is parsed as plain time and "назад" is dropped.
        result = process_phrase('назад 2 месяца', datetime(2024, 1, 15))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.FIXED, date.type)
        self.assertEqual(datetime(2024, 1, 15, 14, 0), date.date_from)

    def test_nazad_with_full_year_span_is_absolute_year(self):
        # Documents current behavior: numbers above 1900 are absolute years,
        # so "назад" is ignored and the year itself is returned.
        result = process_phrase('назад 3000 лет', datetime(2024, 1, 15))
        self.assertEqual(1, len(result.dates))

        date = result.dates[0]
        self.assertEqual(DateTimeTokenType.PERIOD, date.type)
        self.assertEqual(3000, date.date_from.year)
        self.assertEqual(3000, date.date_to.year)
