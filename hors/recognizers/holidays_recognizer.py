"""
Recognizer for weekend words ('выходной', 'на выходных').
"""

from datetime import datetime
from re import Match

from .recognizer import Recognizer
from ..dict import Keywords, Morph, LemmaSearchOptions
from ..models import DatesRawData, TextToken
from .recognizer import Recognizer


class HolidaysRecognizer(Recognizer):
    """
    Recognizes weekend words ('выходной/выходные', pattern 'W') and rewrites them
    into weekday word tokens so DayOfWeekRecognizer can resolve them later.
    """
    regex_pattern = r'W'

    def parse_match(self, data: DatesRawData, match: Match[str], now: datetime) -> bool:
        """
        Replace the single 'W' slot with plain weekday word tokens.

        A singular 'выходной' becomes one Saturday token ('D'); a plural form
        becomes the three words 'суббота до воскресенье' (pattern 'DtD').

        Returns:
            True (the match is consumed and rewritten into word slots).
        """
        s, _ = match.span()
        token = data.tokens[s]
        data.remove_range(s, 1)
        if Morph.has_lemma(token.value, Keywords.HOLIDAY[0], LemmaSearchOptions.ONLY_SINGULAR):
            saturday = TextToken(Keywords.SATURDAY[0], token.start, token.end)
            data.return_tokens(s, 'D', saturday)
        else:
            holidays = [TextToken(h, token.start, token.end) for h in [Keywords.SATURDAY[0], Keywords.TIME_TO[0], Keywords.SUNDAY[0]]]
            data.return_tokens(s, 'DtD', *holidays)
        return True
