from datetime import time

from pydantic import BaseModel


class Timeframe(BaseModel):
    start: time
    end: time

    def __hash__(self):
        return hash((self.start, self.end,))

    def __eq__(self, other):
        return isinstance(other, Timeframe) and other.start == self.start and other.end == self.end

    def __repr__(self):
        return f"Timeframe({self.start}, {self.end})"
