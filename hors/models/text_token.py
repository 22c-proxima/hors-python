"""
TextToken — a single word (or punctuation mark) of the phrase with its position in the source text.
"""

from .i_has_edges import IHasEdges


class TextToken(IHasEdges):
    """A single word (or punctuation mark) of the phrase with its position in the source text."""
    value: str

    def __init__(self, value: str, start: int = 0, end: int = 0) -> None:
        """
        Args:
            value: The token text.
            start: Offset of the first character in the source phrase.
            end: Offset just past the last character (exclusive).
        """
        self.value = value
        self.start = start
        self.end = end
