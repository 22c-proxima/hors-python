import unittest
from datetime import datetime

from hors import process_phrase
from hors.models.parser_models import DateTimeTokenType
from tests.test_base import _datetime_from_str


class ExtraHorsTests(unittest.TestCase):

    def test_from_to_reversed(self):
        result = process_phrase('с 2 до 5', datetime(2019, 10, 13))
        self.assertEqual(1, len(result['dates']))

        date: dict = result['dates'][0]
        self.assertEqual(str(DateTimeTokenType.PERIOD), date['type'])
        date_from = _datetime_from_str(date['date_from'])
        date_to = _datetime_from_str(date['date_to'])
        self.assertEqual(14, date_from.hour)
        self.assertEqual(17, date_to.hour)
        self.assertEqual(13, date_from.day)
        self.assertEqual(13, date_to.day)


if __name__ == '__main__':
    unittest.main()
