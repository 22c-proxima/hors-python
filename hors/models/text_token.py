from .i_has_edges import IHasEdges


class TextToken(IHasEdges):
    value: str

    def __init__(self, value: str, start: int = 0, end: int = 0):
        self.value = value
        self.start = start
        self.end = end
