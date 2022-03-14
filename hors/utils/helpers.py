from typing import List
from string import punctuation


class Helpers:

    @staticmethod
    def trim_punctuation(value: str, leave_valid_symbols: bool = True) -> str:
        # Count start punctuation
        start_offset = 0
        valid_start = '#{[{`"\''
        for c in value:
            if c in punctuation and not(leave_valid_symbols and c in valid_start):
                start_offset += 1
            else:
                break

        # Count end punctuation
        end_offset = 0
        valid_end = '!.?…)]}%"\'`'
        for c in reversed(value):
            if c in punctuation and not(leave_valid_symbols and c in valid_end):
                end_offset -= 1
            else:
                break

        return value[start_offset:end_offset]
    # def trim_punctuation(value: str, leave_valid_symbols: bool = True):

    @staticmethod
    def swap_two(l: List, first_index: int, second_index: int) -> None:
        l[first_index], l[second_index] = l[second_index], l[first_index]
