from typing import List

from ..utils.parser_extractors import ParserExtractors
from .abstract_period import AbstractPeriod
from .i_has_edges import IHasEdges
from .text_token import TextToken


class DatesRawData:
    tokens: List[TextToken]
    pattern: str
    dates: List[AbstractPeriod]

    def __init__(self, tokens) -> None:
        self.pattern = ''.join(map(ParserExtractors.create_pattern_from, tokens))
        self.dates = [None] * len(tokens)

    def get_pattern(self) -> str:
        return self.pattern

    def remove_range(self, start: int, count: int) -> None:
        self.pattern = self.pattern[:start] + self.pattern[start + count:]
        self.tokens = self.tokens[:start] + self.tokens[start + count:]
        self.dates = self.dates[:start] + self.dates[start + count:]

    def insert_dates(self, index: int, *dates: AbstractPeriod) -> None:
        if dates:
            dates_len = len(dates)
            self.dates = self.dates[:index] + list(dates) + self.dates[index:]
            tokens_to_insert = [TextToken('{}')]*dates_len
            self.tokens = self.tokens[:index] + tokens_to_insert + self.tokens[index:]
            pattern_to_insert = '@'*dates_len
            self.pattern = self.pattern[:index] + pattern_to_insert + self.pattern[index:]

    def replace_tokens_by_dates(self, start: int, count: int, *dates: AbstractPeriod) -> None:
        start_index = self.tokens[start].start
        end_index = self.tokens[start + count - 1].end
        for date in dates:
            if date.end == 0:
                date.set_edges(start_index, end_index)
        self.remove_range(start, count)
        self.insert_dates(start, *dates)

    def return_tokens(self, index: int, pattern: str, *tokens: TextToken) -> None:
        self.dates = self.dates[:index] + [None]*len(tokens) + self.dates[index:]
        self.tokens = self.tokens[:index] + list(tokens) + self.tokens[index:]
        self.pattern = self.pattern[:index] + pattern + self.pattern[index:]

    def edges_by_index(self, index: int) -> IHasEdges:
        date = self.dates[index]
        return self.tokens[index] if date is None else date

    def create_tokens(self, tokens: List[str]) -> None:
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
