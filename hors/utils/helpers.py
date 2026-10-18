"""
Misc small utilities: punctuation trimming for the final text and list manipulation.
"""

from typing import List
from string import punctuation


class Helpers:
    """Small static utilities shared across the library."""

    @staticmethod
    def trim_punctuation(value: str, leave_valid_symbols: bool = True) -> str:
        """
        Strip leading/trailing punctuation from value.

        With leave_valid_symbols (default) symbols that may legitimately belong to a
        phrase are kept: '#' and quotes/brackets at the start, sentence-ending marks
        ('.', '!', '?', '…') and closing brackets at the end. Used to clean up the
        reconstructed text in HorsParseResult.
        """
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

        return value[start_offset:len(value) + end_offset]
    # def trim_punctuation(value: str, leave_valid_symbols: bool = True):

    @staticmethod
    def swap_two(l: List, first_index: int, second_index: int) -> None:
        """Swap two elements of a list in place."""
        l[first_index], l[second_index] = l[second_index], l[first_index]
