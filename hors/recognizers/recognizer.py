"""Base class shared by all date-expression recognizers.

A recognizer watches the pattern string (one character per phrase slot, built
by ParserExtractors.create_pattern_from) with a fixed regex and converts each
match into AbstractPeriod slots inside DatesRawData.
"""
from typing import List, Set, Callable, Any
from datetime import datetime
from re import finditer, Match

from ..models import DatesRawData


# Callable returning the current pattern text; called again after every change so rescans see updates.
StrProvider = Callable[[], str]
# Called with each regex match; must return True when the matched slots were consumed (replaced by dates).
RecognizerMatcher = Callable[[Any], bool]


class Recognizer:
    """
    Base class for all date-expression recognizers.

    Subclasses set `regex_pattern` — a regex over the pattern string, where every
    phrase slot is one character produced by ParserExtractors.create_pattern_from
    (e.g. 'M' month word, 'D' weekday word, 'Y' the word "год", '0'/'1' numeric
    tokens, '@' an already matched date).

    parse_match is invoked for every regex hit in the current pattern and should
    build AbstractPeriod objects and call data.replace_tokens_by_dates().
    Returning False leaves the slots unclaimed (and marks the position as skipped).
    """
    regex_pattern: str

    def parse_match(self, data: DatesRawData, match: Match[str], now: datetime) -> bool:
        """
        Handle one regex hit in the pattern string.

        Args:
            data: Working state of the parsing pass.
            match: re.Match against data.get_pattern().
            now: Reference moment for relative expressions.

        Returns:
            True when the matched slots were consumed (replaced by dates).
        """
        return False

    def parse_tokens(self, data: DatesRawData, now: datetime) -> None:
        """
        Run this recognizer over the current pattern string.

        Args:
            data: Working state of the parsing pass.
            now: Reference moment for relative expressions.
        """
        Recognizer.for_all_matches(data.get_pattern, self.regex_pattern, lambda m: self.parse_match(data, m, now))

    @staticmethod
    def for_all_matches(input: StrProvider, pattern: str, action: RecognizerMatcher, reversed: bool = False) -> None:
        """
        Apply `action` to regex matches one by one, rescanning after every change.

        The pattern text is re-fetched through `input`, so the scan reflects slot
        mutations made by earlier actions (dates inserted or words restored).
        When `action(match)` returns False the match position is remembered in
        indexes_to_skip and skipped on rescan, so a rejected match is never retried.

        Args:
            input: Callable returning the current pattern text.
            pattern: Regex to search for.
            action: Called with each match; should return True when it consumed the matched slots.
            reversed: When True matches are processed right-to-left and positions are counted from the end of the string.
        """
        text = input()
        matches: List[Any] = list(finditer(pattern, text))
        if not matches:
            return

        match = matches[-1] if reversed else matches[0]
        indexes_to_skip: Set[int] = set()
        while match:
            text = input()
            s, _ = match.span()
            match_index = len(text) - s if reversed else s
            if not action(match):
                indexes_to_skip.add(match_index)
            match = None
            text = input()
            matches = list(finditer(pattern, text))
            for i in range(len(matches)):
                index = -i - 1 if reversed else i
                s1, _ = matches[index].span()
                match_index = len(text) - s1 if reversed else s1
                if match_index not in indexes_to_skip:
                    match = matches[index]
                    break
