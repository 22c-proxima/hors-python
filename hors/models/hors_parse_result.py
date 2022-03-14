from typing import List, Dict, Set, Any
from re import sub

from ..utils import Helpers
from .parser_models import DateTimeToken


class HorsParseResult:
    source_text: str
    tokens: List[str]
    text: str
    dates: List[DateTimeToken]

    __full_dates: List[DateTimeToken]
    __tokens_to_remove: Set[str] = set()

    def __init__(self, source_text: str, tokens: List[str], dates: List[DateTimeToken]) -> None:
        self.source_text = source_text
        self.__full_dates = dates
        self.dates = self.__create_dates(dates)
        self.tokens = [t for t in tokens if t not in self.__tokens_to_remove]
        self.text = Helpers.trim_punctuation(self.__create_text(False)).strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source_text,
            'tokens': self.tokens,
            'text': self.text,
            'dates': [d.to_dict() for d in self.dates]
        }

    def __create_dates(self, dates: List[DateTimeToken]) -> List[DateTimeToken]:
        duplicate_seen: Set[int] = set()
        result: List[DateTimeToken] = []

        for i, date in enumerate(dates):
            if date.get_duplicate_group() == -1:
                result.append(date)
            elif date.get_duplicate_group() in duplicate_seen:
                self.__tokens_to_remove.add(f'{{{i}}}')
            else:
                duplicate_seen.add(date.get_duplicate_group())
                result.append(date)

        return result

    def __create_text(self, insert: bool) -> str:
        text = self.source_text
        skipped: Set[DateTimeToken] = set()

        for date in reversed(self.__full_dates):
            if date in skipped:
                continue
            same_dates = [d for d in self.__full_dates if d.start == date.start and d not in skipped]
            tokens_to_insert: List[str] = []

            for o_date in same_dates:
                skipped.add(o_date)
                tokens_to_insert.append(f'{{{ self.__full_dates.index(o_date) }}}')

            insert_text = ' '.join(tokens_to_insert) if insert and date in self.dates else ''
            text = text[:date.start] + insert_text + text[date.end:]

        return sub(r'\s{2,}', ' ', text.strip())

    def __str__(self) -> str:
        return f'{ " ".join(self.tokens) }|{ "; ".join(str(d) for d in self.dates) }'

