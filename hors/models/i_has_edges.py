"""
IHasEdges — base for objects that occupy a [start, end) character range of the source phrase.
"""

class IHasEdges:
    """Base for objects that occupy a [start, end) character range of the source phrase."""
    start: int
    end: int

    def set_edges(self, start: int, end: int) -> None:
        """
        Set the character offsets of this object in the source phrase.

        Args:
            start: Offset of the first character.
            end: Offset just past the last character (exclusive).
        """
        self.start = start
        self.end = end
