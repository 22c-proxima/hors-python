"""
HorsParseResult — the public container returned by process_phrase().
"""

from typing import List, Dict, Set, Any
from re import sub

from ..utils import Helpers
from .parser_models import DateTimeToken


class HorsParseResult:
    """
    Result of parsing a phrase into date/time tokens (returned by process_phrase).

    Fields:
        source_text: the phrase this result was built from;
        tokens: the phrase tokens in order, where every matched date region is
            replaced by a placeholder entry like '{0}' (one per kept date), so
            words and dates stay aligned with their positions in the phrase;
        text: the phrase with all date expressions removed, whitespace collapsed
            and leading/trailing punctuation trimmed;
        dates: deduplicated DateTimeToken objects, each carrying start/end
            character offsets into source_text.

    Dates merged from several source expressions share a duplicate_group; only
    the first one of each group is kept in `dates`, the rest are dropped along
    with their placeholder tokens.
    """
    source_text: str
    tokens: List[str]
    text: str
    dates: List[DateTimeToken]

    __full_dates: List[DateTimeToken]
    __tokens_to_remove: Set[str] = set()

    def __init__(self, source_text: str, tokens: List[str], dates: List[DateTimeToken]) -> None:
        """
        Build the public result from raw parser output.

        Args:
            source_text: The phrase as received by the parser.
            tokens: Token strings with date regions already replaced by '{i}' placeholders.
            dates: All resolved DateTimeToken objects, including duplicates.
        """
        self.source_text = source_text
        self.__full_dates = dates
        self.dates = self.__create_dates(dates)
        self.tokens = [t for t in tokens if t not in self.__tokens_to_remove]
        self.text = Helpers.trim_punctuation(self.__create_text(False)).strip()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the result to a plain dict.

        Returns:
            A JSON-serializable dict with keys 'source', 'tokens', 'text' and
            'dates'; each date is serialized via DateTimeToken.to_dict.
        """
        return {
            'source': self.source_text,
            'tokens': self.tokens,
            'text': self.text,
            'dates': [d.to_dict() for d in self.dates]
        }

    def __create_dates(self, dates: List[DateTimeToken]) -> List[DateTimeToken]:
        """
        Drop duplicate dates, keeping only the first of each duplicate_group.

        Placeholder tokens ('{i}') of dropped duplicates are recorded so they
        get removed from `tokens` as well.
        """
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
        """
        Rebuild text by splicing out (or in) every date region of source_text.

        Args:
            insert: When True, a placeholder like '{0}' is inserted at the position
                of each kept date; when False, the date regions are removed.
        """
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
        """
        Human-readable form: tokens joined by spaces, then dates separated by '; '.
        """
        return f'{ " ".join(self.tokens) }|{ "; ".join(str(d) for d in self.dates) }'

