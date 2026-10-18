"""
DatesRawData — working state of one parsing pass: the phrase split into slots
that recognizers rewrite and query by pattern.
"""

from typing import List, Optional

from ..utils.parser_extractors import ParserExtractors
from .abstract_period import AbstractPeriod
from .i_has_edges import IHasEdges
from .text_token import TextToken


class DatesRawData:
    """
    Working state of one parsing pass: the phrase split into slots, each of which
    is either a plain word (TextToken) or a matched date (AbstractPeriod).

    Fields:
        tokens: slot list; a matched date region occupies '{}' placeholder tokens;
        pattern: single-character view of the same slots ('@' for a date slot,
            other chars for words); this is the regex haystack recognizers search;
        dates: parallel list of AbstractPeriod objects, None where the slot is
            a plain word.

    The three structures always stay aligned by index: tokens[i], dates[i] and
    pattern[i] describe the same position.
    """
    tokens: List[TextToken]
    pattern: str
    dates: List[Optional[AbstractPeriod]]

    def __init__(self, tokens: List[str]) -> None:
        """
        Create empty state for a phrase.

        Args:
            tokens: The phrase split into word strings; defines the slot count
                and the initial pattern (one char per word). Token objects and
                dates are filled in later via create_tokens().
        """
        self.pattern = ''.join(map(ParserExtractors.create_pattern_from, tokens))
        self.dates = [None] * len(tokens)

    def get_pattern(self) -> str:
        """
        Returns:
            The current pattern string (the regex haystack for recognizers).
        """
        return self.pattern

    def remove_range(self, start: int, count: int) -> None:
        """
        Remove a slice of slots from all parallel structures.

        Args:
            start: Index of the first slot to remove.
            count: Number of consecutive slots to remove.
        """
        self.pattern = self.pattern[:start] + self.pattern[start + count:]
        self.tokens = self.tokens[:start] + self.tokens[start + count:]
        self.dates = self.dates[:start] + self.dates[start + count:]

    def insert_dates(self, index: int, *dates: AbstractPeriod) -> None:
        """
        Insert one slot per period at `index`.

        Each period gets a '{}' placeholder token, an '@' pattern char and its
        own dates entry. The periods themselves are not mutated here.

        Args:
            index: Position in the token list where the slots go.
            *dates: Periods to insert (one slot each).
        """
        if dates:
            dates_len = len(dates)
            self.dates = self.dates[:index] + list(dates) + self.dates[index:]
            tokens_to_insert = [TextToken('{}')]*dates_len
            self.tokens = self.tokens[:index] + tokens_to_insert + self.tokens[index:]
            pattern_to_insert = '@'*dates_len
            self.pattern = self.pattern[:index] + pattern_to_insert + self.pattern[index:]

    def replace_tokens_by_dates(self, start: int, count: int, *dates: AbstractPeriod) -> None:
        """
        Replace a run of word tokens with date slots (the core recognizer operation).

        The token range [start, start+count) is removed and the given periods are
        inserted in its place; every period whose end edge is still 0 gets its
        start/end set to the character offsets of the replaced run.

        Args:
            start: Index of the first token of the matched expression.
            count: Number of tokens the expression spans.
            *dates: Periods created for the match (one slot each).
        """
        start_index = self.tokens[start].start
        end_index = self.tokens[start + count - 1].end
        for date in dates:
            if date.end == 0:
                date.set_edges(start_index, end_index)
        self.remove_range(start, count)
        self.insert_dates(start, *dates)

    def return_tokens(self, index: int, pattern: str, *tokens: TextToken) -> None:
        """
        Restore plain word slots at `index` (undoing a date match).

        Args:
            index: Position in the token list where the words go back.
            pattern: Pattern chars for the restored tokens (one per token).
            *tokens: TextTokens to restore.
        """
        self.dates = self.dates[:index] + [None]*len(tokens) + self.dates[index:]
        self.tokens = self.tokens[:index] + list(tokens) + self.tokens[index:]
        self.pattern = self.pattern[:index] + pattern + self.pattern[index:]

    def edges_by_index(self, index: int) -> IHasEdges:
        """
        Returns:
            The object occupying slot `index`: an AbstractPeriod if a date was
            matched there, otherwise the TextToken itself; both expose start/end.
        """
        date = self.dates[index]
        return self.tokens[index] if date is None else date

    def create_tokens(self, tokens: List[str]) -> None:
        """
        Build the token list from raw word strings (once per parsing pass).

        Args:
            tokens: The phrase split into word strings; character offsets are
                computed with one separator character between words.

        Also drops stray '0' tokens that immediately precede a single digit.
        """
        self.tokens = []
        l = 0
        for token in tokens:
            len_token = len(token)
            self.tokens.append(TextToken(token, l, l + len_token))
            l += len_token + 1  # +1 for separator symbol

        i = 0
        while i < len(self.tokens) - 1:
            if self.tokens[i].value == '0' and len(self.tokens[i + 1].value) == 1 and self.tokens[i + 1].value.isdigit():
                self.remove_range(i, 1)
            else:
                i += 1
