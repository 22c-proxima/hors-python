class IHasEdges:
    start: int
    end: int

    def set_edges(self, start: int, end: int) -> None:
        self.start = start
        self.end = end
