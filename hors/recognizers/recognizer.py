from typing import List, Set, Callable, Any
from datetime import datetime
from re import finditer

from ..models import DatesRawData


StrProvider = Callable[[], str]
RecognizerMatcher = Callable[[Any], bool]


class Recognizer:
    regex_pattern: str

    def parse_match(self, data: DatesRawData, match, now: datetime):
        pass

    def parse_tokens(self, data: DatesRawData, now: datetime) -> None:
        Recognizer.for_all_matches(data.get_pattern, self.regex_pattern, lambda m: self.parse_match(data, m, now))

    @staticmethod
    def for_all_matches(input: StrProvider, pattern: str, action: RecognizerMatcher, reversed: bool = False) -> None:
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
